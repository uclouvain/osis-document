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
import re

import uuid
from django import forms
from django.conf import settings
from django.contrib.postgres.forms import SplitArrayWidget
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

from osis_document.enums import TokenAccess
from osis_document.utils import get_token


class FileUploadWidget(SplitArrayWidget):
    template_name = 'osis_document/uploader_widget.html'

    class Media:
        css = {
            'all': ('osis_document/osis-document.css',)
        }
        js = ('osis_document/osis-document.umd.min.js',)

    def __init__(self, **kwargs):
        self.automatic_upload = kwargs.pop('automatic_upload', True)
        self.mimetypes = kwargs.pop('mimetypes', None)
        self.max_size = kwargs.pop('max_size', None)
        self.upload_button_text = kwargs.pop('upload_button_text', None)
        self.upload_text = kwargs.pop('upload_text', None)
        self.can_edit_filename = kwargs.pop('can_edit_filename', True)
        if kwargs.get('size', None) is None:
            kwargs['size'] = 0
        super().__init__(widget=forms.TextInput, **kwargs)

    def value_from_datadict(self, data, files, name):
        return [self.widget.value_from_datadict(data, files, '%s_%s' % (name, index))
                for index in range(self.get_size(data, name))]

    @staticmethod
    def get_size(data, name):
        # Detect the size of the array by sorting prefixed data and getting the last number via regex
        names = sorted([field_name for field_name in data if field_name.startswith(name)], reverse=True)
        if names:
            search = re.findall(r'\d+', names[0]) or ['-1']
            return int(search[-1]) + 1
        return 0

    def value_omitted_from_data(self, data, files, name):
        fn = all if self.size else any
        return fn(
            self.widget.value_omitted_from_data(data, files, '%s_%s' % (name, index))
            for index in range(self.get_size(data, name))
        )

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        if not getattr(settings, 'OSIS_DOCUMENT_BASE_URL', None):
            raise ImproperlyConfigured(_("Missing OSIS_DOCUMENT_BASE_URL setting"))
        attrs['data-limit'] = self.size
        attrs['data-base-url'] = settings.OSIS_DOCUMENT_BASE_URL
        if self.mimetypes:
            attrs['data-mimetypes'] = ','.join(self.mimetypes)
        if not self.automatic_upload:
            attrs['data-automatic-upload'] = "false"
        if self.can_edit_filename is False:
            attrs['data-editable-filename'] = "false"
        if self.max_size is not None:
            attrs['data-max-size'] = self.max_size
        if self.upload_button_text is not None:
            attrs['data-upload-button-text'] = self.upload_button_text
        if self.upload_text is not None:
            attrs['data-upload-text'] = self.upload_text
        return attrs

    def format_value(self, values):
        # Values is an array of either tokens or uuid, or None
        # Convert the uuid values to write tokens, and filter out None values
        return filter(None, [
            get_token(value, access=TokenAccess.WRITE.name) if isinstance(value, uuid.UUID) else value
            for value in values
        ])
