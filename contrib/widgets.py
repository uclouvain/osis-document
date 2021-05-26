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

from django import forms
from django.conf import settings
from django.contrib.postgres.forms import SplitArrayWidget
from django.urls import reverse


class FileUploadWidget(SplitArrayWidget):
    # TODO set data-attributes on rendering for VueJS
    template_name = 'osis_document/uploader_widget.html'

    class Media:
        css = {
            'all': ('osis_document/osis-document.css',)
        }
        js = ('osis_document/osis-document.umd.min.js',)

    def __init__(self, max_size=None, mimetypes=None, upload_text='', **kwargs):
        self.upload_text = upload_text
        self.mimetypes = mimetypes
        self.max_size = max_size
        super().__init__(widget=forms.TextInput, **kwargs)

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        upload_url = getattr(settings, 'OSIS_DOCUMENT_UPLOAD_URL', None)
        attrs['data-upload-url'] = upload_url or reverse('osis_document:request-upload')
        if self.mimetypes is not None:
            attrs['data-mimetypes'] = json.dumps(self.mimetypes)
        if self.max_size is not None:
            attrs['data-max-size'] = self.max_size
        return attrs

    def format_value(self, value):
        return value
