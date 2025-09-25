# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.translation import gettext_lazy as _
from osis_document.enums import DocumentError
from rest_framework import status
from rest_framework.exceptions import APIException


class TokenNotFound(APIException):
    status_code = 404
    default_detail = "Token not found."
    default_code = "not_found"


class FileReferenceNotFound(APIException):
    status_code = 404
    default_detail = "File reference not found."
    default_code = "not_found"


class TokenExpired(APIException):
    status_code = 403
    default_detail = "Token has expired."
    default_code = "token_expired"


class HashMismatch(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = DocumentError.HASH_MISMATCH.value


class MimeMismatch(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = DocumentError.MIME_MISMATCH.value


class FileInfectedException(APIException):
    default_detail = DocumentError.INFECTED.value


class UploadInvalidException(APIException):
    default_detail = _("Invalid upload UUID")


class FormatInvalidException(APIException):
    default_detail = _("Invalid file format")


class ConversionError(APIException):
    default_detail = _("Error during file conversion to pdf")


class MissingFileException(APIException):
    default_detail = _("Error during getting input files")


class InvalidPostProcessorAction(APIException):
    default_detail = _("Invalid post_processing action")


class InvalidMergeFileDimension(APIException):
    default_detail = _("Invalid dimension params given for merge action")


class SaveRawContentRemotelyException(Exception):
    def __init__(self, api_response):
        self.api_response = api_response
        self.message = f"An error occured during uploading file to OSIS-Document server. Error:{self.api_response.text}"
        super().__init__(self.message)
