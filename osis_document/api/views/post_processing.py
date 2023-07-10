from osis_document.api import serializers
from osis_document.api.schema import DetailedAutoSchema
from osis_document.enums import PostProcessingStatus
from osis_document.models import PostProcessAsync
from osis_document.utils import post_process, create_post_process_async_object
from rest_framework import status
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.response import Response
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
                if validated_data["async_post_processing"]:
                    create_post_process_async_object(
                        uuid_list=validated_data["files_uuid"],
                        post_process_actions=validated_data["post_process_types"],
                        post_process_params=validated_data["post_process_params"],
                    )
                    return Response(status=status.HTTP_202_ACCEPTED)
                else:
                    uuids_result_dict = post_process(
                        uuid_list=validated_data["files_uuid"],
                        post_process_actions=validated_data["post_process_types"],
                        post_process_params=validated_data["post_process_params"],
                    )
                    return Response(data=uuids_result_dict, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status.HTTP_400_BAD_REQUEST)


class GetProgressAsyncPostProcessingSchema(AutoSchema):
    serializer_mapping = {
        'POST': serializers.ProgressAsyncPostProcessingSerializer,
    }

    def get_operation_id(self, path, method):
        return 'get-progress-post-processing'

    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        operation['security'] = [{"ApiKeyAuth": []}]
        return operation


class GetProgressAsyncPostProcessingView(APIView):
    name = 'get-progress-post-processing'
    authentication_classes = []
    permission_classes = []

    def post(self, *args, **kwargs):
        try:
            input_serializer_data = serializers.ProgressAsyncPostProcessingSerializer(
                data=self.request.data,
            )

            if input_serializer_data.is_valid(raise_exception=True):
                validated_data = input_serializer_data.validated_data
                async_post_process = PostProcessAsync.objects.get(uuid=validated_data['pk'])
                wanted_post_processing = validated_data['wanted_post_process']
                result = {
                    'progress': None,
                    'wanted_post_process_status': None
                }
                if wanted_post_processing:
                    result['wanted_post_process_status'] = async_post_process.results[wanted_post_processing]['status']
                if async_post_process.status == PostProcessingStatus.FAILED.name:
                    result['failed'] = True
                result['progress'] = self.get_progress(async_post_process_object=async_post_process)
                return Response(data=result, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response({'error': str(e)}, status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def get_progress(async_post_process_object: PostProcessAsync) -> int:
        action_list = async_post_process_object.data.get('post_process_actions')
        pourcentage_par_action = 100 / len(action_list)
        result = 0
        for action in action_list:
            if async_post_process_object.results[action]["status"] == PostProcessingStatus.DONE.name:
                result += pourcentage_par_action
        return result
