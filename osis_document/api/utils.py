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
from urllib.parse import urlparse

from django.conf import settings
from django.utils.module_loading import import_string
from rest_framework.views import APIView


class CorsAllowOriginMixin(APIView):
    ACCESS_CONTROL_ALLOW_ORIGIN = "Access-Control-Allow-Origin"
    ACCESS_CONTROL_ALLOW_METHODS = "Access-Control-Allow-Methods"
    ACCESS_CONTROL_ALLOW_HEADERS = "Access-Control-Allow-Headers"

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)

        response[self.ACCESS_CONTROL_ALLOW_METHODS] = "GET, POST"
        response[self.ACCESS_CONTROL_ALLOW_HEADERS] = "Content-Type"

        origin = request.META.get("HTTP_ORIGIN")
        if not origin:
            return response

        if self.origin_found_in_white_lists(urlparse(origin)):
            response[self.ACCESS_CONTROL_ALLOW_ORIGIN] = origin

        return response

    def origin_found_in_white_lists(self, url):
        origins = [urlparse(o) for o in settings.OSIS_DOCUMENT_DOMAIN_LIST]
        return any(origin.scheme == url.scheme and origin.netloc == url.netloc for origin in origins)


def get_raw_file_view():
    return import_string(settings.RAW_FILE_VIEW)

def get_metadata_view():
    return import_string(settings.METADATA_VIEW)

def get_several_metadata_view():
    return import_string(settings.SEVERAL_METADATA_VIEW)

def get_change_metadata_view():
    return import_string(settings.CHANGE_METADATA_VIEW)
