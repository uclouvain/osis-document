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

    def __init__(self, max_size=None, mimetypes=None, automatic_upload=True, **kwargs):
        self.automatic_upload = automatic_upload
        self.mimetypes = mimetypes
        self.max_size = max_size
        super().__init__(widget=forms.TextInput, **kwargs)

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
        if self.max_size is not None:
            attrs['data-max-size'] = self.max_size
        return attrs

    def format_value(self, value):
        # Convert the raw value (which is a list of uuids) to a list of write tokens
        return [
            get_token(uuid, access=TokenAccess.WRITE.name)
            for uuid in value
        ]
