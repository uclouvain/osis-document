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

from os.path import dirname

from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.validators import ArrayMinLengthValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from osis_document.contrib.forms import FileUploadField
from osis_document.utils import generate_filename
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

        kwargs.setdefault('default', list)
        kwargs.setdefault('base_field', models.UUIDField())
        kwargs.setdefault('size', self.max_files)
        super().__init__(**kwargs)
        self.default_validators = [*self.default_validators, TokenValidator(self.error_messages['invalid_token'])]
        if self.min_files and not self.blank and not self.null:
            self.default_validators = [*self.default_validators, ArrayMinLengthValidator(self.min_files)]

    def formfield(self, **kwargs):
        """Transfer all properties to the form field"""
        return super(ArrayField, self).formfield(**{
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
            **kwargs,
        })

    def pre_save(self, model_instance, add):
        """Convert all writing tokens to UUIDs by remotely confirming their upload, leaving existing uuids"""
        value = [
            self._confirm_upload(model_instance, token) if isinstance(token, str) else token
            for token in (getattr(model_instance, self.attname) or [])
        ]
        setattr(model_instance, self.attname, value)
        if self.post_processing:
            self._post_processing(uuid_list=value)
        return value

    def _confirm_upload(self, model_instance, token):
        """Call the remote API to confirm the upload of a token"""
        from osis_document.api.utils import confirm_remote_upload, get_remote_metadata

        # Get the current filename by interrogating API
        filename = get_remote_metadata(token)['name']
        return confirm_remote_upload(
            token=token,
            upload_to=dirname(generate_filename(model_instance, filename, self.upload_to)),
        )

    def _post_processing(self, uuid_list: list):
        from osis_document.api.utils import launch_post_processing
        return launch_post_processing(uuid_list=[uuid_list], post_processing_types=self.post_processing)
