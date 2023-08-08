# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
import sys
from io import BytesIO

import filetype
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from osis_document.api import serializers
from osis_document.api.schema import DetailedAutoSchema
from osis_document.api.utils import CorsAllowOriginMixin
from osis_document.enums import TokenAccess
from osis_document.exceptions import MimeMismatch
from osis_document.models import Token
from osis_document.utils import calculate_hash, get_token


class SaveEditorSchema(DetailedAutoSchema):  # pragma: no cover
    serializer_mapping = {
        'POST': (serializers.SaveEditorSerializer, serializers.SaveEditorResponseSerializer),
    }

    def get_operation_id(self, path, method):
        return 'saveEditor'

    def get_responses(self, path, method):
        responses = super().get_responses(path, method)
        responses['200'] = responses.pop('201')
        return responses


class SaveEditorView(CorsAllowOriginMixin, APIView):
    """Receive a file (from VueJS), rotate its pages if needed and replace corresponding upload"""

    name = 'save-editor'
    authentication_classes = []
    permission_classes = []
    parser_classes = [MultiPartParser]
    schema = SaveEditorSchema()

    def post(self, request, *args, **kwargs):
        token = get_object_or_404(
            Token.objects.writing_not_expired(),
            token=self.kwargs['token'],
        )
        upload = token.upload

        if upload.mimetype != 'application/pdf':
            return Response({'error': _("File is not a PDF")}, status=status.HTTP_400_BAD_REQUEST)

        serializer = serializers.SaveEditorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data['file']

        # Process file: rotate pages if needed
        if serializer.validated_data['rotations']:
            from pypdf import PdfWriter

            temp_bytes = BytesIO()
            writer = PdfWriter(temp_bytes, clone_from=file.file)
            for page_index, angle in serializer.validated_data['rotations'].items():
                writer.pages[int(page_index)].rotate(angle)
            writer.write(temp_bytes)
            temp_bytes.seek(0)
            file = InMemoryUploadedFile(
                temp_bytes,
                None,
                file.name,
                file.content_type,
                sys.getsizeof(temp_bytes),
                None,
            )

        # Process file: calculate hash and save it to db
        bytesa = file.file.read(4096)
        file.file.seek(0)
        fileguess = filetype.guess(bytesa)
        if fileguess.mime != file.content_type or file.content_type != 'application/pdf':
            raise MimeMismatch
        upload.file.save(upload.file.name, file)
        upload.size = file.size
        upload.metadata['hash'] = calculate_hash(file)
        upload.save()

        # Regenerate new token
        token.delete()
        token = get_token(upload.uuid, access=TokenAccess.WRITE.name)
        return Response({'token': token}, status=status.HTTP_200_OK)
