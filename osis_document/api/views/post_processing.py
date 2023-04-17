from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from osis_document.api import serializers
from osis_document.api.schema import DetailedAutoSchema
from osis_document.utils import post_process


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
    schema = PostProcessingSchema

    def post(self, *args, **kwargs):
        try:
            input_serializer_data = serializers.PostProcessing(data={
                **self.request.data,
            })
            validated_data = input_serializer_data.is_valid(raise_exception=True)
            uuids_result_dict = post_process(uuid_list=validated_data["files_uuid"],
                                             post_process_type=validated_data["post_process_type"])
            return Response(data=uuids_result_dict, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status.HTTP_400_BAD_REQUEST)
