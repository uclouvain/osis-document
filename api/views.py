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
from rest_framework import generics

from osis_document.api.serializers import TokenSerializer, MetadataSerializer, UploadUUIDSerializer
from osis_document.models import Upload, Token
from osis_document.utils import confirm_upload


class GetTokenView(generics.CreateAPIView):
    serializer_class = TokenSerializer
    name = 'get-token'
    queryset = Upload.objects.all()

    def create(self, request, *args, **kwargs):
        upload = self.get_object()
        request.data['upload_id'] = upload.pk
        return super().create(request, *args, **kwargs)


class MetadataView(generics.RetrieveAPIView):
    serializer_class = MetadataSerializer
    name = 'get-metadata'
    queryset = Upload.objects.all()


class ConfirmUploadView(generics.UpdateAPIView):
    serializer_class = UploadUUIDSerializer
    name = 'confirm-upload'
    lookup_field = 'token'
    queryset = Token.objects.writing_not_expired()

    def perform_update(self, serializer):
        confirm_upload(serializer.instance.token)