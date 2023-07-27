# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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


class PostProcessingNotPending(APIException):
    default_detail = _("This post-processing does not have status pending ")
