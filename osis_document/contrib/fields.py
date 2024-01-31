# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
import uuid
from os.path import dirname
from typing import Set, List, Union

from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.validators import ArrayMinLengthValidator
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import gettext_lazy as _
from uuid import UUID

from osis_document.contrib.forms import FileUploadField
from osis_document.utils import generate_filename
from osis_document.enums import DocumentExpirationPolicy
from osis_document.validators import TokenValidator


class FileField(ArrayField):
    """This is the model field that handle storage of UUIDs"""

    default_error_messages = {
        'invalid_token': _("Invalid token"),
    }

    def __init__(self, **kwargs):
        self.automatic_upload = kwargs.pop('automatic_upload', True)
        self.can_edit_filename = kwargs.pop('can_edit_filename', True)
        self.max_size = kwargs.pop('max_size', None)
        self.mimetypes = kwargs.pop('mimetypes', None)
        self.upload_button_text = kwargs.pop('upload_button_text', None)
        self.upload_text = kwargs.pop('upload_text', None)
        self.max_files = kwargs.pop('max_files', None)
        self.min_files = kwargs.pop('min_files', None)
        self.upload_to = kwargs.pop('upload_to', '')
        self.post_processing = kwargs.pop('post_processing', [])
        self.async_post_processing = kwargs.pop('async_post_processing', False)
        self.output_post_processing = kwargs.pop('output_post_processing', None)
        self.post_process_params = kwargs.pop('post_process_params', None)
        self.document_expiration_policy = kwargs.pop(
            'document_expiration_policy',
            DocumentExpirationPolicy.NO_EXPIRATION.value,
        )
        self.with_cropping = kwargs.pop('with_cropping', False)
        self.cropping_options = kwargs.pop('cropping_options', None)

        kwargs.setdefault('default', list)
        kwargs.setdefault('base_field', models.UUIDField())
        kwargs.setdefault('size', self.max_files)
        super().__init__(**kwargs)
        self.default_validators = [*self.default_validators, TokenValidator(self.error_messages['invalid_token'])]
        if self.min_files and not self.blank and not self.null:
            self.default_validators = [*self.default_validators, ArrayMinLengthValidator(self.min_files)]

    def formfield(self, **kwargs):
        """Transfer all properties to the form field"""
        return super(ArrayField, self).formfield(
            **{
                'form_class': FileUploadField,
                'max_size': self.max_size,
                'min_files': self.min_files,
                'max_files': self.max_files,
                'mimetypes': self.mimetypes,
                'automatic_upload': self.automatic_upload,
                'can_edit_filename': self.can_edit_filename,
                'upload_button_text': self.upload_button_text,
                'upload_text': self.upload_text,
                'upload_to': self.upload_to,
                'post_processing': self.post_processing,
                'async_post_processing': self.async_post_processing,
                'output_post_processing': self.output_post_processing,
                'post_process_params': self.post_process_params,
                'with_cropping': self.with_cropping,
                'cropping_options': self.cropping_options,
                **kwargs,
            }
        )

    def pre_save(self, model_instance, add):
        """
        Convert all writing tokens to UUIDs by remotely confirming their upload, leaving existing uuids
        and deleting old documents
        """
        try:
            previous_values = self.model.objects.values_list(self.attname).get(pk=model_instance.pk)[0] or []
        except ObjectDoesNotExist:
            previous_values = []

        attvalues = getattr(model_instance, self.attname) or []
        files_confirmed = self._confirm_multiple_upload(model_instance, attvalues, previous_values)
        if self.post_processing:
            self._post_processing(uuid_list=files_confirmed)
        setattr(model_instance, self.attname, files_confirmed)
        return files_confirmed

    def _confirm_multiple_upload(
        self,
        model_instance,
        attvalues: List[Union[str, UUID]],
        previous_values: List[UUID],
    ):
        """Call the remote API to confirm multiple upload and delete old file if replaced"""
        from osis_document.api.utils import confirm_remote_upload, get_several_remote_metadata, \
            declare_remote_files_as_deleted

        files_to_keep = [token for token in attvalues if not isinstance(token, str)]  # UUID

        tokens = [token for token in attvalues if isinstance(token, str)]
        metadata_by_token = get_several_remote_metadata(tokens) if tokens else {}
        for token in tokens:
            filename = metadata_by_token[token]['name']
            file_uuid = confirm_remote_upload(
                token=token,
                upload_to=dirname(generate_filename(model_instance, filename, self.upload_to)),
                document_expiration_policy=self.document_expiration_policy,
            )
            files_to_keep.append(UUID(file_uuid))

        files_to_declare_as_deleted = set(previous_values) - set(files_to_keep)
        if files_to_declare_as_deleted:
            declare_remote_files_as_deleted(files_to_declare_as_deleted)
        return files_to_keep

    def _post_processing(self, uuid_list: list):
        from osis_document.api.utils import launch_post_processing
        return launch_post_processing(
            async_post_processing=self.async_post_processing,
            uuid_list=[uuid_list] if not isinstance(uuid_list, list) else uuid_list,
            post_processing_types=self.post_processing,
            post_process_params=self.post_process_params
        )
