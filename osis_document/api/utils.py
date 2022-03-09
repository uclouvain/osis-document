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

import json
from typing import Union
from urllib.error import HTTPError
from urllib.parse import urlparse

from django.conf import settings
from rest_framework.views import APIView

from osis_document.exceptions import UploadConfirmationException


def get_remote_metadata(token: str) -> Union[dict, None]:
    from urllib import request
    url = "{}metadata/{}".format(settings.OSIS_DOCUMENT_BASE_URL, token)
    try:
        with request.urlopen(url) as f:
            return json.loads(f.read().decode('utf-8'))
    except HTTPError:
        return None


def get_remote_token(uuid, write_token=False):
    from urllib import request
    url = "{base_url}{token_type}-token/{uuid}".format(
        base_url=settings.OSIS_DOCUMENT_BASE_URL,
        token_type='write' if write_token else 'read',
        uuid=uuid,
    )
    req = request.Request(url, method='POST')
    req.add_header('X-Api-Key', settings.OSIS_DOCUMENT_API_SHARED_SECRET)
    try:
        with request.urlopen(req) as f:
            return json.loads(f.read().decode('utf-8')).get('token')
    except HTTPError:
        return None


def confirm_remote_upload(token, upload_to=None, related_model=None, related_model_instance=None):
    from urllib import request
    url = "{}confirm-upload/{}".format(settings.OSIS_DOCUMENT_BASE_URL, token)
    data = {}
    # Add facultative params
    if upload_to:
        # The 'upload_to' property is explicitly defined as a string
        data['upload_to'] = upload_to
    elif related_model:
        # The 'upload_to' property will be automatically computed in api side
        instance_filter_fields = related_model.pop('instance_filter_fields', None)
        if instance_filter_fields and related_model_instance:
            # And will be based on a specific instance
            related_model['instance_filters'] = {
                key: getattr(related_model_instance, key, None) for key in instance_filter_fields
            }
        data['related_model'] = related_model

    # Create the request
    req = request.Request(url, method='POST', data=json.dumps(data).encode('utf8'))
    req.add_header('X-Api-Key', settings.OSIS_DOCUMENT_API_SHARED_SECRET)
    req.add_header('Content-Type', "application/json")
    try:
        with request.urlopen(req) as f:
            return json.loads(f.read().decode('utf-8')).get('uuid')
    except HTTPError as e:
        raise UploadConfirmationException(e.filename, e.code, e.reason, e.headers, e.fp)


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
        return any(
            origin.scheme == url.scheme and origin.netloc == url.netloc
            for origin in origins
        )
