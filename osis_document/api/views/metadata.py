from django.http import Http404
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from osis_document.api import serializers
from osis_document.api.schema import DetailedAutoSchema
from osis_document.api.utils import CorsAllowOriginMixin
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


class MetadataView(CorsAllowOriginMixin, APIView):
    """Get metadata for an upload given a token"""
    name = 'get-metadata'
    authentication_classes = []
    permission_classes = []
    schema = MetadataSchema()

    def get(self, *args, **kwargs):
        metadata = get_metadata(self.kwargs['token'])
        if not metadata:
            raise Http404
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


class ChangeMetadataView(CorsAllowOriginMixin, APIView):
    """Change metadata from a writing token"""
    name = 'change-metadata'
    authentication_classes = []
    permission_classes = []
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
