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
from typing import Union, List, Dict
from urllib.parse import urlparse

from django.conf import settings
from osis_document.exceptions import FileInfectedException, UploadInvalidException
from requests import HTTPError
from rest_framework import status
from rest_framework.views import APIView


def get_remote_metadata(token: str) -> Union[dict, None]:
    """Given a token, return the remote metadata."""
    import requests

    url = "{}metadata/{}".format(settings.OSIS_DOCUMENT_BASE_URL, token)
    try:
        response = requests.get(url)
        if response.status_code is not status.HTTP_200_OK:
            return None
        return response.json()
    except HTTPError:
        return None


def get_several_remote_metadata(tokens: List[str]) -> Dict[str, dict]:
    """Given a list of tokens, return a dictionary associating each token to upload metadata."""
    import requests

    url = "{}metadata".format(settings.OSIS_DOCUMENT_BASE_URL)
    try:
        response = requests.post(
            url,
            json=tokens,
            headers={'X-Api-Key': settings.OSIS_DOCUMENT_API_SHARED_SECRET},
        )

        if response.status_code == status.HTTP_200_OK:
            return response.json()
    except HTTPError:
        pass
    return {}


def get_raw_content_remotely(token: str):
    """Given a token, return the file raw."""
    import requests

    try:
        response = requests.get(f"{settings.OSIS_DOCUMENT_BASE_URL}file/{token}")
        if response.status_code is not status.HTTP_200_OK:
            return None
        return response.content
    except HTTPError:
        return None


def get_remote_token(uuid, write_token=False):
    """Given an uuid, return a writing or reading remote token."""
    import requests

    url = "{base_url}{token_type}-token/{uuid}".format(
        base_url=settings.OSIS_DOCUMENT_BASE_URL,
        token_type='write' if write_token else 'read',
        uuid=uuid,
    )
    try:
        response = requests.post(url, headers={'X-Api-Key': settings.OSIS_DOCUMENT_API_SHARED_SECRET})
        if response.status_code == status.HTTP_404_NOT_FOUND:
            return UploadInvalidException.__class__.__name__
        json = response.json()
        if (
                response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                and json['detail'] == FileInfectedException.default_detail
        ):
            return FileInfectedException.__class__.__name__
        return json.get('token')
    except HTTPError:
        return None


def get_remote_tokens(uuids: List[str]) -> Dict[str, str]:
    """Given a list of uuids, return a dictionary associating each uuid to a reading token."""
    import requests

    url = "{base_url}read-tokens".format(base_url=settings.OSIS_DOCUMENT_BASE_URL)
    try:
        response = requests.post(
            url,
            json=uuids,
            headers={'X-Api-Key': settings.OSIS_DOCUMENT_API_SHARED_SECRET},
        )
        if response.status_code == status.HTTP_201_CREATED:
            return {uuid: item.get('token') for uuid, item in response.json().items() if 'error' not in item}
    except HTTPError:
        pass
    return {}


def confirm_remote_upload(token, upload_to=None, related_model=None, related_model_instance=None):
    import requests

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

    # Do the request
    response = requests.post(
        url,
        json=data,
        headers={'X-Api-Key': settings.OSIS_DOCUMENT_API_SHARED_SECRET},
    )
    return response.json().get('uuid')


def launch_post_processing(uuid_list: List, post_processing_types: List, post_process_params: Dict):
    import requests

    url = "{}post-processing".format(settings.OSIS_DOCUMENT_BASE_URL)
    data = {'post_process_types': post_processing_types,
            'files_uuid': uuid_list,
            'post_process_params': post_process_params
            }
    response = requests.post(
        url,
        json=data,
        headers={'X-Api-Key': settings.OSIS_DOCUMENT_API_SHARED_SECRET},
    )
    return response.json()


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
