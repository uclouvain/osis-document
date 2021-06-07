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
from django import forms
from django.contrib.postgres.forms import SplitArrayField
from django.utils.translation import gettext_lazy as _

from osis_document.contrib.widgets import FileUploadWidget
from osis_document.utils import get_metadata


class TokenOrUuidField(forms.CharField):
    default_error_messages = {
        'nonexistent': _("File upload is either non-existent or has expired"),
        'size': _("File upload is too large"),
        'mimetype': _("Bad file upload mimetype"),
    }

    def __init__(self, max_size=None, mimetypes=None, **kwargs):
        self.max_size = max_size
        self.mimetypes = mimetypes
        kwargs['max_length'] = 1024
        super().__init__(**kwargs)

    def clean(self, value):
        cleaned_data = super().clean(value)
        # Check file presence, size and mimetype
        metadata = get_metadata(cleaned_data)
        if not metadata:
            raise forms.ValidationError(self.error_messages['nonexistent'], code='nonexistent')
        if self.max_size is not None and metadata['size'] > self.max_size:
            raise forms.ValidationError(self.error_messages['size'], code='size')
        if self.mimetypes is not None and metadata['mimetype'] not in self.mimetypes:
            raise forms.ValidationError(self.error_messages['mimetype'], code='mimetype')
        return cleaned_data


class FileUploadField(SplitArrayField):
    def __init__(self, limit=None, max_size=None, mimetypes=None, upload_text='', automatic_upload=True, **kwargs):
        self.upload_text = upload_text
        self.mimetypes = mimetypes
        self.max_size = max_size
        kwargs.setdefault('widget', FileUploadWidget(
            max_size=max_size,
            mimetypes=mimetypes,
            automatic_upload=automatic_upload,
            size=limit or 1,
        ))
        base_field = TokenOrUuidField(
            required=True,
            max_size=max_size,
            mimetypes=mimetypes,
        )
        kwargs.setdefault('base_field', base_field)
        kwargs.setdefault('size', limit or 1)
        super().__init__(**kwargs)

    @staticmethod
    def persist(values):
        from osis_document.utils import confirm_upload
        return [confirm_upload(token) for token in values]
