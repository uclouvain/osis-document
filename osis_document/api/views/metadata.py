from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from osis_document.api.schema import DetailedAutoSchema
from osis_document.exceptions import Md5Mismatch
from osis_document.api import serializers
from osis_document.models import Token
from osis_document.utils import get_metadata


class MetadataSchema(DetailedAutoSchema):  # pragma: no cover
    serializer_mapping = {
        'GET': serializers.MetadataSerializer,
    }

    def get_responses(self, path, method):
        responses = super().get_responses(path, method)
        responses['409'] = {
            "description": "Conflict",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/Error"
                    }
                }
            }
        }
        return responses


class MetadataView(APIView):
    """Get metadata for an upload given a token"""
    name = 'get-metadata'
    authentication_classes = []
    permission_classes = []
    schema = MetadataSchema()

    def get(self, *args, **kwargs):
        try:
            metadata = get_metadata(self.kwargs['token'])
        except Md5Mismatch:
            return Response({
                'error': _("MD5 checksum mismatch")
            }, status.HTTP_409_CONFLICT)
        if not metadata:
            return Response({
                'error': _("Resource not found")
            }, status.HTTP_404_NOT_FOUND)
        return Response(metadata)


class ChangeMetadataSchema(DetailedAutoSchema):  # pragma: no cover
    serializer_mapping = {
        'POST': (serializers.ChangeMetadataSerializer, None),
    }

    def get_operation_id(self, path, method):
        return 'changeMetadata'

    def get_responses(self, path, method):
        responses = super().get_responses(path, method)
        responses['200'] = responses.pop('201')
        return responses


class ChangeMetadataView(APIView):
    """Change metadata from a writing token"""
    name = 'change-metadata'
    authentication_classes = []
    permission_classes = []
    http_method_names = ['post']
    schema = ChangeMetadataSchema()

    def post(self, *args, **kwargs):
        token = get_object_or_404(
            Token.objects.writing_not_expired(),
            token=self.kwargs['token'],
        )
        upload = token.upload
        upload.metadata['name'] = self.request.data.get('name', '')
        upload.save()
        return Response(status=status.HTTP_200_OK)
