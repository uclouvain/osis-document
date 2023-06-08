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

from django import template
from django.conf import settings

from osis_document.utils import (
    get_file_url as utils_get_file_url,
)

register = template.Library()


@register.inclusion_tag('osis_document/visualizer.html')
def document_visualizer(values):
    from osis_document.api.utils import get_remote_token

    return {
        'values': [get_remote_token(value) for value in values],
        'base_url': settings.OSIS_DOCUMENT_BASE_URL,
    }


@register.inclusion_tag('osis_document/editor.html')
def document_editor(value, **attrs):
    from osis_document.api.utils import get_remote_token
    return {
        'value': get_remote_token(value, write_token=True),
        'base_url': settings.OSIS_DOCUMENT_BASE_URL,
        'attrs': attrs,
    }


@register.simple_tag
def get_metadata(uuid, type_post_processing=None):
    from osis_document.api.utils import get_remote_metadata, get_remote_token
    return get_remote_metadata(get_remote_token(uuid=uuid, type_post_processing=type_post_processing))


@register.simple_tag
def get_file_url(uuid, type_post_processing=None):
    from osis_document.api.utils import get_remote_token
    return utils_get_file_url(get_remote_token(uuid=uuid, type_post_processing=type_post_processing))

