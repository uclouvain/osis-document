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
    get_token,
    get_metadata as utils_get_metadata,
    get_file_url as utils_get_file_url,
)

register = template.Library()


@register.inclusion_tag('osis_document/visualizer.html')
def document_visualizer(values):
    return {
        'values': [get_token(value) for value in values],
        'base_url': settings.OSIS_DOCUMENT_BASE_URL,
    }


@register.simple_tag
def get_metadata(uuid):
    return utils_get_metadata(get_token(uuid))


@register.simple_tag
def get_file_url(uuid):
    return utils_get_file_url(get_token(uuid))
