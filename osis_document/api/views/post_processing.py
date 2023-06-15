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
        'POST': (None, serializers.PostProcessing),
    }

    def get_operation_id(self, path, method):
        return 'postProcessing'

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
            input_serializer_data = serializers.PostProcessing(
                data={
                    **self.request.data,
                }
            )
            validated_data = input_serializer_data.is_valid(raise_exception=True)
            if validated_data:
                if input_serializer_data.data["async_post_processing"] == True:
                    create_post_process_async_object(
                        uuid_list=input_serializer_data.data["files_uuid"],
                        post_process_actions=input_serializer_data.data["post_process_types"],
                        post_process_params=input_serializer_data.data["post_process_params"],
                    )
                    return Response(status=status.HTTP_202_ACCEPTED)
                else:
                    uuids_result_dict = post_process(
                        uuid_list=input_serializer_data.data["files_uuid"],
                        post_process_actions=input_serializer_data.data["post_process_types"],
                        post_process_params=input_serializer_data.data["post_process_params"],
                    )
                    return Response(data=uuids_result_dict, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status.HTTP_400_BAD_REQUEST)


class GetProgressAsyncPostProcessingSchema(AutoSchema):
    pass


class GetProgressAsyncPostProcessingView(APIView):
    name = 'get-progress-post-processing'
    authentication_classes = []
    permission_classes = []

    def post(self, *args, **kwargs):
        async_post_process = PostProcessAsync.objects.get(uuid=self.request.data.get('uuid'))
        wanted_post_processing = self.request.data.get('wanted_post_process')
        result = {'progress': None,
                  'wanted_post_process_status': None}
        if async_post_process:
            if async_post_process.status == PostProcessingStatus.DONE.name:
                result['progress'] = 100
                if wanted_post_processing:
                    result['wanted_post_process_status'] = PostProcessingStatus.DONE.name
            elif async_post_process.status in [PostProcessingStatus.PENDING.name, PostProcessingStatus.FAILED.name]:
                if wanted_post_processing:
                    result['wanted_post_process_status'] = async_post_process.results[wanted_post_processing]['status']
                if async_post_process.status == PostProcessingStatus.FAILED.name:
                    result['failed'] = True
                result['progress'] = self.get_progress(async_post_process_object=async_post_process)
            return Response(data=result, status=status.HTTP_202_ACCEPTED)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def get_progress(async_post_process_object: PostProcessAsync) -> int:
        action_list = async_post_process_object.data.get('post_process_actions')
        pourcentage_par_action = 100 / len(action_list)
        result = 0
        for action in action_list:
            if async_post_process_object.results[action]["status"] == PostProcessingStatus.DONE.name:
                result += pourcentage_par_action
        return result

