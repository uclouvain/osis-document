from osis_document.api import serializers
from osis_document.api.schema import DetailedAutoSchema
from osis_document.enums import PostProcessingStatus
from osis_document.models import PostProcessingController
from osis_document.tasks import make_one_pending_post_processing
from osis_document.utils import create_post_processing_controller_object
from rest_framework import status
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.views import APIView


class PostProcessingSchema(DetailedAutoSchema):
    serializer_mapping = {
        'POST': serializers.PostProcessingSerializer,
    }

    def get_operation_id(self, path, method):
        return 'request-post-processing'

    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        operation['security'] = [{"ApiKeyAuth": []}]
        return operation


class PostProcessingView(APIView):
    name = 'request-post-processing'
    authentication_classes = []
    permission_classes = []
    schema = PostProcessingSchema()

    def post(self, *args, **kwargs):
        try:
            input_serializer_data = serializers.PostProcessingSerializer(
                data={
                    **self.request.data,
                }
            )
            if input_serializer_data.is_valid(raise_exception=True):
                validated_data = input_serializer_data.data
                post_processing_controller_instance = create_post_processing_controller_object(
                    uuid_list=validated_data["files_uuid"],
                    post_process_actions=validated_data["post_process_types"],
                    post_process_params=validated_data["post_process_params"],
                )
                if validated_data["async_post_processing"]:
                    return Response(status=status.HTTP_202_ACCEPTED)
                else:
                    uuids_result_dict = make_one_pending_post_processing(
                        uuid=post_processing_controller_instance.uuid
                    )
                    return Response(data=uuids_result_dict, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status.HTTP_400_BAD_REQUEST)


class GetProgressPostProcessingControllerSchema(AutoSchema):
    serializer_mapping = {

        'GET': serializers.ProgressAsyncPostProcessingSerializer,
    }

    def get_operation_id(self, path, method):
        return 'get-progress-post-processing'

    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        operation['security'] = [{"ApiKeyAuth": []}]
        return operation


class GetProgressPostProcessingControllerView(APIView):
    name = 'get-progress-post-processing'
    authentication_classes = []
    permission_classes = []

    def get(self, *args, **kwargs):
        try:
            input_serializer_data = serializers.ProgressAsyncPostProcessingSerializer(
                data={'pk': self.kwargs.get('pk'), },
            )

            if input_serializer_data.is_valid(raise_exception=True):
                validated_data = input_serializer_data.validated_data
                post_processing_controller = PostProcessingController.objects.get(uuid=validated_data['pk'])
                wanted_post_processing = validated_data['wanted_post_process']
                result = {
                    'progress': None,
                    'wanted_post_process_status': None
                }
                if wanted_post_processing:
                    result['wanted_post_process_status'] = post_processing_controller.results[wanted_post_processing]['status']
                if post_processing_controller.status == PostProcessingStatus.FAILED.name:
                    result['failed'] = True
                result['progress'] = self.get_progress(post_processing_controller_object=post_processing_controller)
                return Response(data=result, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response({'error': str(e)}, status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def get_progress(post_processing_controller_object: PostProcessingController) -> int:
        action_list = post_processing_controller_object.data.get('post_process_actions')
        pourcentage_par_action = 100 / len(action_list)
        result = 0
        for action in action_list:
            if post_processing_controller_object.results[action]["status"] == PostProcessingStatus.DONE.name:
                result += pourcentage_par_action
        return result
