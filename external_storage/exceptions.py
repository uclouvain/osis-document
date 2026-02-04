# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from rest_framework.exceptions import APIException


class ExternalStorageAPICallException(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY


class ExternalStorageAPICallTimeout(ExternalStorageAPICallException):
    default_detail = "External storage API call timed out."
    default_code = "external_storage_api_timeout"


class FileReferenceNotFound(APIException):
    status_code = 404
    default_detail = "File reference not found."
    default_code = "not_found"

class TokenNotFound(APIException):
    status_code = 404
    default_detail = "Token not found."
    default_code = "not_found"


class TokenExpired(APIException):
    status_code = 403
    default_detail = "Token has expired."
    default_code = "token_expired"
