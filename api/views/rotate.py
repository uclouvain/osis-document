# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################

import hashlib
from io import BytesIO

from PIL import Image
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _
from osis_document.api import serializers
from osis_document.api.schema import DetailedAutoSchema
from osis_document.api.utils import CorsAllowOriginMixin
from osis_document.enums import TokenAccess
from osis_document.models import Token
from osis_document.utils import get_token
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView


class RotateImageSchema(DetailedAutoSchema):  # pragma: no cover
    serializer_mapping = {
        'POST': (serializers.RotateImageSerializer, serializers.RotateImageResponseSerializer),
    }

    def get_operation_id(self, path, method):
        return 'rotateImage'

    def get_responses(self, path, method):
        responses = super().get_responses(path, method)
        responses['200'] = responses.pop('201')
        return responses


class RotateImageView(CorsAllowOriginMixin, APIView):
    """Rotate an image from a writing token"""

    name = 'rotate-image'
    authentication_classes = []
    permission_classes = []
    schema = RotateImageSchema()

    def post(self, *args, **kwargs):
        token = get_object_or_404(
            Token.objects.writing_not_expired(),
            token=self.kwargs['token'],
        )
        upload = token.upload

        if upload.mimetype.split('/')[0] != 'image':
            return Response({'error': _("File is not an image")}, status=status.HTTP_400_BAD_REQUEST)

        rotated_photo = BytesIO()
        image = Image.open(upload.file)
        original_format = image.format
        image = image.rotate(-self.request.data.get('rotate', 0), expand=True)
        image.save(rotated_photo, original_format)

        upload.file.save(upload.file.name, ContentFile(rotated_photo.getvalue()))

        hash = hashlib.sha256()
        with upload.file.open('rb') as file:
            for chunk in file.chunks():
                hash.update(chunk)
        upload.metadata['hash'] = hash.hexdigest()
        upload.save()

        # Regenerate new token
        token.delete()
        token = get_token(upload.uuid, access=TokenAccess.WRITE.name)
        return Response({'token': token}, status=status.HTTP_200_OK)
