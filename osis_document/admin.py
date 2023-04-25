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
from django.contrib import admin
from django.template.defaultfilters import filesizeformat
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from osis_document.models import Token, Upload, PostProcessing


class UploadAdmin(admin.ModelAdmin):
    list_display = [
        'uuid',
        'file_button',
        'uploaded_at',
        'status',
        'display_size',
        'mimetype',
    ]
    date_hierarchy = 'uploaded_at'
    list_filter = [
        'status',
        'mimetype',
    ]

    def file_button(self, obj):
        return format_html('<a href="{}" target="_blank" class="button">&nbsp;&gt;&nbsp;</a>', obj.file.url)

    file_button.short_description = _('File')

    def display_size(self, obj):
        return filesizeformat(obj.size)

    display_size.short_description = _('Size')


class TokenAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'access',
        'created_at',
        'upload',
    ]
    date_hierarchy = 'created_at'
    list_filter = [
        'access',
        'upload__status',
    ]


class PostProcessingAdmin(admin.ModelAdmin):
    list_display = [
        'uuid',
        'created_at',
        'type',
    ]
    date_hierarchy = 'created_at'
    list_filter = [
        'type',
    ]


admin.site.register(Upload, UploadAdmin)
admin.site.register(Token, TokenAdmin)
admin.site.register(PostProcessing, PostProcessingAdmin)
