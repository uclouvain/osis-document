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

from django.core import signing
from django.core.exceptions import FieldError
from django.forms import modelform_factory
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from osis_document.enums import TokenAccess
from osis_document.models import Upload, Token

__all__ = [
    'RequestUploadView',
    'ConfirmUploadView',
    'change_metadata',
    'rotate_upload',
    'get_file_url',
    'get_file',
    'get_metadata',
]

from osis_document.utils import confirm_upload


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

            # Create a token based on uuid and md5
            token = signing.dumps({
                'uuid': str(instance.uuid),
                'md5': md5,
            })
            Token.objects.create(
                upload=instance,
                access=TokenAccess.WRITE,
                token=token,
            )
            return Response({'token': token}, status.HTTP_201_CREATED)
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


def change_metadata(request):
    raise NotImplementedError


def rotate_upload(request):
    raise NotImplementedError


def get_file_url(request):
    raise NotImplementedError


def get_file(request):
    # TODO check md5 integrity between metadata and file
    raise NotImplementedError


def get_metadata(request, token_or_uuid: str):
    raise NotImplementedError
