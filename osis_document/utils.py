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
import contextlib
import datetime
import hashlib
import posixpath
import sys
import uuid
from typing import Union, List, Dict
from uuid import UUID

from django.conf import settings
from django.core import signing
from django.core.exceptions import FieldError
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _
from osis_document.enums import FileStatus, PostProcessingStatus, PostProcessingType, DocumentExpirationPolicy
from osis_document.exceptions import HashMismatch, InvalidPostProcessorAction, SaveRawContentRemotelyException
from osis_document.models import Token, Upload, PostProcessAsync


def confirm_upload(token, upload_to, document_expiration_policy=None, model_instance=None) -> UUID:
    """Verify local token existence and expiration"""
    token = Token.objects.writing_not_expired().filter(token=token).select_related('upload').first()
    if not token:
        raise FieldError(_("Token non-existent or expired"))

    # Delete token
    upload = token.upload
    token.delete()

    # Set upload as persisted, move the related file to a specified location and return the upload uuid
    if upload.status != FileStatus.UPLOADED.name:
        upload.status = FileStatus.UPLOADED.name
        # Create a file with the new name at the specified location
        previous_file_name = upload.file.name
        new_file_name = generate_filename(
            instance=model_instance,
            filename=upload.metadata['name'],
            upload_to=upload_to,
        )
        upload.file.open()
        upload.file.save(name=new_file_name, content=upload.file.file, save=False)
        # Remove the file at the previous location
        upload.file.storage.delete(previous_file_name)
        upload.expires_at = DocumentExpirationPolicy.compute_expiration_date(document_expiration_policy)
        upload.save()
    return upload.uuid


def get_file_url(token: str) -> str:
    """Get the raw file url given a token"""
    # We can not use reverse because the potential prefix would be present twice
    return '{base_url}file/{token}'.format(
        base_url=settings.OSIS_DOCUMENT_BASE_URL,
        token=token,
    )


def generate_filename(instance, filename, upload_to):
    """
    Apply (if callable) or prepend (if a string) upload_to to the filename. If you specify a string value,
    it may contain strftime() formatting, which will be replaced by the date/time of the file upload.
    """
    if callable(upload_to):
        filename = upload_to(instance, filename)
    elif upload_to:
        dirname = datetime.datetime.now().strftime(upload_to)
        filename = posixpath.join(dirname, filename)
    return filename


def get_upload_metadata(token: str, upload: Upload):
    return {
        'size': upload.size,
        'mimetype': upload.mimetype,
        'name': upload.file.name,
        'url': get_file_url(token),
        'uploaded_at': upload.uploaded_at,
        'upload_uuid': upload.uuid,
        **upload.metadata,
    }


def get_metadata(token: str):
    upload = Upload.objects.from_token(token)
    if not upload:
        return None
    with upload.file.open() as file:
        hash = hashlib.sha256(file.read()).hexdigest()
    if upload.metadata.get('hash') != hash:
        raise HashMismatch()
    return get_upload_metadata(token, upload)


def get_token(uuid, **kwargs):
    return Token.objects.create(
        upload_id=uuid,
        token=signing.dumps(str(uuid)),
        **kwargs,
    ).token


def is_uuid(value: Union[str, uuid.UUID]) -> bool:
    if isinstance(value, uuid.UUID):
        return True
    with contextlib.suppress(ValueError, AttributeError):
        uuid.UUID(hex=value)
        return True
    return False


def calculate_hash(file):
    hash = hashlib.sha256()
    if isinstance(file, bytes):
        hash.update(file)
    else:
        for chunk in file.chunks():
            hash.update(chunk)
    return hash.hexdigest()


def save_raw_upload(file, name, mimetype, **metadata):
    """Save a file into a local Upload object with given parameters."""

    hash = calculate_hash(file)
    upload = Upload.objects.create(
        mimetype=mimetype,
        size=sys.getsizeof(file),
        metadata={"hash": hash, 'name': name, **metadata},
    )
    upload.file.save(
        content=ContentFile(file),
        name=name,
        save=True,
    )
    # create a related token
    token = Token.objects.create(
        upload_id=upload.uuid,
        token=signing.dumps(str(upload.uuid)),
    )
    return token


def save_raw_content_remotely(content: bytes, name: str, mimetype: str):
    """Save a raw file by sending it over the network."""
    import requests

    url = "{}request-upload".format(settings.OSIS_DOCUMENT_BASE_URL)
    data = {'file': (name, content, mimetype)}

    # Create the request
    response = requests.post(url, files=data)
    if response.status_code != 201:
        raise SaveRawContentRemotelyException(response)
    return response.json().get('token')


def post_process(
        uuid_list: List[UUID],
        post_process_actions: List[str],
        post_process_params: Dict[str, Dict[str, str]],
) -> Dict[str, Dict[str, List[UUID]]]:
    """
    Given a list of uuids and a list of post-processing actions and a dictionary of params for each post-processing
    action, return a dictionary containing uuid of input and output for each post-processing action.
    """
    from osis_document.contrib.post_processing.converter_registry import converter_registry
    from osis_document.contrib.post_processing.merger import merger

    post_processing_return = {}
    post_processing_return.setdefault(PostProcessingType.CONVERT.name, {'input': [], 'output': []})
    post_processing_return.setdefault(PostProcessingType.MERGE.name, {'input': [], 'output': []})
    intermediary_output = {}

    processors = {
        PostProcessingType.CONVERT.name: converter_registry,
        PostProcessingType.MERGE.name: merger,
    }

    for action_type in post_process_actions:
        processor = processors.get(action_type, None)
        if not processor:
            raise InvalidPostProcessorAction
        input = post_processing_return[action_type]["input"] = intermediary_output[
            'upload_objects'] if intermediary_output else uuid_list
        intermediary_output = processor.process(upload_objects_uuids=input, **post_process_params[action_type])
        post_processing_return[action_type]["output"] = intermediary_output

    return post_processing_return


def create_post_process_async_object(
        uuid_list: List[UUID],
        post_process_actions: List[str],
        post_process_params: Dict[str, Dict[str, str]],
) -> None:
    """
    Create a PostProcessingAsync object with the list of uuid, the list of post-processing actions and the
    post-processing params dictionary
    """
    PostProcessAsync.objects.create(
        status=PostProcessingStatus.PENDING.name,
        data={'post_process_actions': post_process_actions,
              'base_input': uuid_list,
              'post_process_params': post_process_params},
        results={
            action: {'status': PostProcessingStatus.PENDING.name} for action in post_process_actions
        }
    )


def stringify_uuid_and_check_uuid_validity(uuid_input: Union[str, UUID]) -> Dict[str, Union[str, bool]]:
    """
    Checks the validity of an uuid and converts it to a string if necessary
    """
    results = {
        'uuid_valid': False,
        'uuid_stringify': '',
    }
    if isinstance(uuid_input, str):
        try:
            uuid.UUID(uuid_input)
            results['uuid_valid'] = True
            results['uuid_stringify'] = uuid_input
        except ValueError:
            results['valid'] = False
    elif isinstance(uuid_input, UUID):
        results['uuid_valid'] = True
        results['uuid_stringify'] = str(uuid_input)
    else:
        raise TypeError
    return results
