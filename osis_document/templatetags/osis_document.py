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

from osis_document.enums import PostProcessingWanted, PostProcessingStatus
from osis_document.utils import (
    get_file_url as utils_get_file_url,
)

register = template.Library()


@register.inclusion_tag('osis_document/visualizer.html')
def document_visualizer(values, wanted_post_process=None, for_modified_upload=False):
    from osis_document.api.utils import get_remote_token
    tokens = []
    for value in values:
        token = get_remote_token(
            value,
            wanted_post_process=wanted_post_process,
            for_modified_upload=for_modified_upload,
        )
        if isinstance(token, dict):
            return {
                'values': '',
                'base_uuid': str(value),
                'wanted_post_process': wanted_post_process,
                'post_process_status': token.get('status'),
                'base_url': settings.OSIS_DOCUMENT_BASE_URL,
                'get_progress_url': token.get("links").get('progress'),
            }
        elif wanted_post_process == PostProcessingWanted.MERGE.name:
            return {
                'values': [token],
                'post_process_status': PostProcessingStatus.DONE.name,
                'base_url': settings.OSIS_DOCUMENT_BASE_URL,
            }
        else:
            tokens.append(token)
    return {
        'values': tokens,
        'post_process_status': '',
        'base_url': settings.OSIS_DOCUMENT_BASE_URL,
    }


@register.inclusion_tag('osis_document/editor.html')
def document_editor(value, for_modified_upload=False, **attrs):
    from osis_document.api.utils import get_remote_token
    return {
        'value': get_remote_token(value, write_token=True, for_modified_upload=for_modified_upload),
        'base_url': settings.OSIS_DOCUMENT_BASE_URL,
        'attrs': attrs,
    }


@register.simple_tag
def get_metadata(uuid, wanted_post_process=None, custom_ttl=None, for_modified_upload=False):
    from osis_document.api.utils import get_remote_metadata, get_remote_token
    return get_remote_metadata(
        get_remote_token(
            uuid=uuid,
            wanted_post_process=wanted_post_process,
            custom_ttl=custom_ttl,
            for_modified_upload=for_modified_upload,
        )
    )


@register.simple_tag
def get_file_url(uuid, wanted_post_process=None, custom_ttl=None, for_modified_upload=False):
    from osis_document.api.utils import get_remote_token
    return utils_get_file_url(
        get_remote_token(
            uuid=uuid,
            wanted_post_process=wanted_post_process,
            custom_ttl=custom_ttl,
            for_modified_upload=for_modified_upload,
        )
    )
