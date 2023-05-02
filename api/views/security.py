# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from osis_document.api import serializers
from osis_document.api.permissions import APIKeyPermission
from osis_document.api.schema import DetailedAutoSchema
from osis_document.enums import FileStatus


class DeclareFileAsInfectedSchema(DetailedAutoSchema):  # pragma: no cover
    serializer_mapping = {
        'POST': (serializers.DeclareFileAsInfectedSerializer, serializers.ConfirmUploadResponseSerializer),
    }

    def get_operation_id(self, path, method):
        return 'declareFileAsInfected'

    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        operation['security'] = [{"ApiKeyAuth": []}]
        return operation


class DeclareFileAsInfectedView(APIView):
    name = 'declare-file-as-infected'
    authentication_classes = []
    permission_classes = [APIKeyPermission]
    schema = DeclareFileAsInfectedSchema()

    def post(self, *args, **kwargs):
        """Given a server-to-server request, declare the file as infected"""
        input_serializer_data = serializers.DeclareFileAsInfectedSerializer(data={
                **self.request.data,
        })
        input_serializer_data.is_valid(raise_exception=True)
        validated_data = input_serializer_data.validated_data
        upload = validated_data.get('path')
        upload.status = FileStatus.INFECTED.name
        upload.save()
        return Response({'uuid': upload.uuid}, status.HTTP_202_ACCEPTED)
