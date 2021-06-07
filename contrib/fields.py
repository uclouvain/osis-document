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
from django.contrib.postgres.fields import ArrayField
from django.db import models

from osis_document.contrib.forms import FileUploadField
from osis_document.utils import confirm_upload


class FileField(ArrayField):
    def __init__(self, max_size=None, limit=None, mimetypes=None, upload_text='', automatic_upload=True, **kwargs):
        self.automatic_upload = automatic_upload
        self.max_size = max_size
        self.upload_text = upload_text
        self.mimetypes = mimetypes
        kwargs.setdefault('default', list)
        kwargs.setdefault('base_field', models.UUIDField())
        kwargs.setdefault('size', limit)
        super().__init__(**kwargs)

    def formfield(self, **kwargs):
        return super(ArrayField, self).formfield(**{
            'form_class': FileUploadField,
            'max_size': self.max_size,
            'limit': self.size,
            'mimetypes': self.mimetypes,
            'upload_text': self.upload_text,
            'automatic_upload': self.automatic_upload,
            **kwargs,
        })

    def pre_save(self, model_instance, add):
        return [confirm_upload(token) for token in super().pre_save(model_instance, add)]
