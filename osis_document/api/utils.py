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
from uuid import UUID

from django.conf import settings
from osis_document.exceptions import FileInfectedException, UploadInvalidException
from osis_document.enums import DocumentExpirationPolicy
from osis_document.utils import stringify_uuid_and_check_uuid_validity
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


def get_remote_token(uuid: Union[str, UUID], write_token: bool = False, wanted_post_process: str = None, custom_ttl=None, for_modified_upload: bool = False):
    """
    Given an uuid, return a writing or reading remote token.
    The custom_ttl parameter is used to define the validity period of the token
    The wanted_post_process parameter is used to specify which post-processing action you want the output files for
    (example : PostProcessingWanted.CONVERT.name)
    """
    import requests
    is_valid_uuid = stringify_uuid_and_check_uuid_validity(uuid_input=uuid)
    if not is_valid_uuid.get('uuid_valid'):
        return None
    else:
        validated_uuid = is_valid_uuid.get('uuid_stringify')
        url = "{base_url}{token_type}-token/{uuid}".format(
            base_url=settings.OSIS_DOCUMENT_BASE_URL,
            token_type='write' if write_token else 'read',
            uuid=validated_uuid,
        )
        try:
            response = requests.post(
                url,
                json={
                    'uuid': validated_uuid,
                    'wanted_post_process': wanted_post_process,
                    'custom_ttl': custom_ttl,
                    'for_modified_upload': for_modified_upload,
                },
                headers={'X-Api-Key': settings.OSIS_DOCUMENT_API_SHARED_SECRET},
            )
            if response.status_code == status.HTTP_404_NOT_FOUND:
                return UploadInvalidException.__class__.__name__
            json = response.json()
            if (
                    response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                    and json.get('detail', '') == FileInfectedException.default_detail
            ):
                return FileInfectedException.__class__.__name__
            return json.get('token') or json
        except HTTPError:
            return None


def get_remote_tokens(uuids: List[str], wanted_post_process=None, custom_ttl=None, for_modified_upload: bool = False) -> Dict[str, str]:
    """Given a list of uuids, a type of post-processing and a custom TTL in second,
    return a dictionary associating each uuid to a reading token.
    The custom_ttl parameter is used to define the validity period of the token
    The wanted_post_process parameter is used to specify which post-processing action you want the output files for
    (example : PostProcessingWanted.CONVERT.name)
    """
    import requests
    import contextlib
    validated_uuids = []
    for uuid in uuids:
        is_valid_uuid = stringify_uuid_and_check_uuid_validity(uuid_input=uuid)
        if is_valid_uuid.get('uuid_valid'):
            validated_uuids.append(is_valid_uuid.get('uuid_stringify'))
    if len(uuids) != len(validated_uuids):
        raise TypeError
    url = "{base_url}read-tokens".format(base_url=settings.OSIS_DOCUMENT_BASE_URL)
    with contextlib.suppress(HTTPError):
        data = {'uuids': validated_uuids, 'for_modified_upload': for_modified_upload}
        if wanted_post_process:
            data.update({'wanted_post_process': wanted_post_process})
        if custom_ttl:
            data.update({'custom_ttl': custom_ttl})
        response = requests.post(
            url,
            json=data,
            headers={'X-Api-Key': settings.OSIS_DOCUMENT_API_SHARED_SECRET},
        )
        if response.status_code == status.HTTP_201_CREATED:
            return {uuid: item.get('token') for uuid, item in response.json().items() if 'error' not in item}
        if response.status_code in [status.HTTP_206_PARTIAL_CONTENT, status.HTTP_500_INTERNAL_SERVER_ERROR]:
            return response.json()
    return {}


def confirm_remote_upload(
    token,
    upload_to=None,
    document_expiration_policy=DocumentExpirationPolicy.NO_EXPIRATION.value,
    related_model=None,
    related_model_instance=None,
):
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

    if document_expiration_policy:
        data['document_expiration_policy'] = document_expiration_policy

    # Do the request
    response = requests.post(
        url,
        json=data,
        headers={'X-Api-Key': settings.OSIS_DOCUMENT_API_SHARED_SECRET},
    )
    return response.json().get('uuid')


def launch_post_processing(
        uuid_list: List,
        async_post_processing: bool,
        post_processing_types: List[str],
        post_process_params: Dict[str, Dict[str, str]]
):
    import requests

    url = "{}post-processing".format(settings.OSIS_DOCUMENT_BASE_URL)
    data = {'async_post_processing': async_post_processing,
            'post_process_types': post_processing_types,
            'files_uuid': uuid_list,
            'post_process_params': post_process_params
            }
    response = requests.post(
        url,
        json=data,
        headers={'X-Api-Key': settings.OSIS_DOCUMENT_API_SHARED_SECRET},
    )
    return response.json() if not async_post_processing else response


def declare_remote_files_as_deleted(
    uuid_list
):
    import requests

    url = "{}declare-files-as-deleted".format(settings.OSIS_DOCUMENT_BASE_URL)
    data = {'files': uuid_list}
    response = requests.post(
        url,
        json=data,
        headers={'X-Api-Key': settings.OSIS_DOCUMENT_API_SHARED_SECRET},
    )
    return response.json()


def get_progress_async_post_processing(uuid: str, wanted_post_process: str = None):
    """Given an uuid and a type of post-processing,
        returns an int corresponding to the post-processing progress percentage
        The wanted_post_process parameter is used to specify the post-processing action you want to get progress to.
        (example : PostProcessingType.CONVERT.name)
    """
    import requests

    url = "{base_url}get-progress-async-post-processing/{uuid}".format(
        base_url=settings.OSIS_DOCUMENT_BASE_URL,
        uuid=uuid
    )
    response = requests.post(
        url,
        json={'pk': uuid, 'wanted_post_process': wanted_post_process},
        headers={'X-Api-Key': settings.OSIS_DOCUMENT_API_SHARED_SECRET},
    )
    return response.json()


def change_remote_metadata(token, metadata):
    """Update metadata of a remote document and return the updated metadata if successful."""
    import requests

    url = "{}change-metadata/{}".format(settings.OSIS_DOCUMENT_BASE_URL, token)

    response = requests.post(
        url=url,
        json=metadata,
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
