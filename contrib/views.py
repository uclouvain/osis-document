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
from django.core.exceptions import FieldError
from django.core.files.base import ContentFile
from django.forms import modelform_factory
from django.http import FileResponse
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from osis_document.enums import TokenAccess
from osis_document.exceptions import Md5Mismatch
from osis_document.models import Upload, Token
from osis_document.utils import confirm_upload, get_metadata, get_token

__all__ = [
    'RequestUploadView',
    'ConfirmUploadView',
    'RotateImageView',
    'FileView',
    'MetadataView',
    'ChangeMetadataView',
]


class UploadUserThrottle(UserRateThrottle):
    rate = '10/minute'


class RequestUploadView(APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [UploadUserThrottle]
    http_method_names = ['post']

    def post(self, request):
        """
        VueJS endpoint to create an Upload
        :param request:
        :return:
        """
        # Check that the sent data is ok
        form = modelform_factory(Upload, fields=['file'])(request.POST, request.FILES)
        if form.is_valid():

            # Process file: calculate md5 and save it to db
            file = request.FILES['file']
            m = hashlib.md5()
            for chunk in file.chunks():
                m.update(chunk)
            md5 = m.hexdigest()
            instance = Upload(
                file=file,
                mimetype=file.content_type,
                size=file.size,
                metadata={'md5': md5},
            )
            instance.save()

            # Create a write token to allow persistance
            return Response({'token': get_token(instance.uuid)}, status.HTTP_201_CREATED)
        return Response({'errors': form.errors}, status.HTTP_400_BAD_REQUEST)


class ConfirmUploadView(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['post']

    def post(self, request, token: str):
        """
        Endpoint to persists an upload
        :param request:
        :param token:
        :return:
        """
        try:
            uuid = confirm_upload(token)
        except FieldError as e:
            return Response({
                'error': str(e)
            }, status.HTTP_400_BAD_REQUEST)
        return Response({'uuid': uuid}, status.HTTP_201_CREATED)


class ChangeMetadataView(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['post']

    def post(self, request, token: str):
        """Endpoint to change metadata name about an upload"""
        token = get_object_or_404(
            Token,
            token=token,
            access=TokenAccess.WRITE.name,
        )
        upload = token.upload
        upload.metadata['name'] = request.data.get('name', '')
        upload.save()
        return Response(status=status.HTTP_200_OK)


class RotateImageView(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['post']

    def post(self, request, token: str):
        """Endpoint to change metadata name about an upload"""
        token = get_object_or_404(
            Token,
            token=token,
            access=TokenAccess.WRITE.name,
        )
        upload = token.upload

        if upload.mimetype.split('/')[0] != 'image':
            return Response(status=status.HTTP_400_BAD_REQUEST)

        rotated_photo = BytesIO()
        image = Image.open(upload.file)
        original_format = image.format
        image = image.rotate(-request.data.get('rotate', 0), expand=True)
        image.save(rotated_photo, original_format)

        upload.file.save(upload.file.name, ContentFile(rotated_photo.getvalue()))

        md5 = hashlib.md5()
        with upload.file.open('rb') as file:
            for chunk in file.chunks():
                md5.update(chunk)
        upload.metadata['md5'] = md5.hexdigest()
        upload.save()

        # Regenerate new token
        token.delete()
        token = get_token(upload.uuid, access=TokenAccess.WRITE.name)
        return Response({'token': token}, status=status.HTTP_200_OK)


class FileView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, token: str):
        """Endpoint to get real file"""
        upload = Upload.objects.filter(tokens__token=token).first()
        if not upload:
            return Response({
                'error': _("Resource not found")
            }, status.HTTP_404_NOT_FOUND)
        with upload.file.open() as file:
            md5 = hashlib.md5(file.read()).hexdigest()
        if upload.metadata.get('md5') != md5:
            return Response({
                'error': _("MD5 checksum mismatch")
            }, status.HTTP_409_CONFLICT)
        # TODO handle internal nginx redirect based on a setting
        return FileResponse(upload.file.open('rb'))


class MetadataView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, token: str):
        """Endpoint to get metadata about an upload"""
        try:
            metadata = get_metadata(token)
        except Md5Mismatch:
            return Response({
                'error': _("MD5 checksum mismatch")
            }, status.HTTP_409_CONFLICT)
        if not metadata:
            return Response({
                'error': _("Resource not found")
            }, status.HTTP_404_NOT_FOUND)
        return Response(metadata)
