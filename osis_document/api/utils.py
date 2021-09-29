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
from typing import Union
from urllib.error import HTTPError

from django.conf import settings

from osis_document.exceptions import UploadConfirmationException


def get_remote_metadata(token: str) -> Union[dict, None]:
    from urllib import request
    url = "{}metadata/{}".format(settings.OSIS_DOCUMENT_BASE_URL, token)
    try:
        with request.urlopen(url) as f:
            return json.loads(f.read().decode('utf-8'))
    except HTTPError:
        return None


def get_remote_token(uuid, write_token=False):
    from urllib import request
    url = "{base_url}{token_type}-token/{uuid}".format(
        base_url=settings.OSIS_DOCUMENT_BASE_URL,
        token_type='write' if write_token else 'read',
        uuid=uuid,
    )
    req = request.Request(url, method='POST')
    req.add_header('X-Api-Key', settings.OSIS_DOCUMENT_API_SHARED_SECRET)
    try:
        with request.urlopen(req) as f:
            return json.loads(f.read().decode('utf-8')).get('token')
    except HTTPError:
        return None


def confirm_remote_upload(token):
    from urllib import request
    url = "{}confirm-upload/{}".format(settings.OSIS_DOCUMENT_BASE_URL, token)
    req = request.Request(url, method='POST')
    req.add_header('X-Api-Key', settings.OSIS_DOCUMENT_API_SHARED_SECRET)
    try:
        with request.urlopen(req) as f:
            return json.loads(f.read().decode('utf-8')).get('uuid')
    except HTTPError as e:
        raise UploadConfirmationException(e.filename, e.code, e.msg, e.headers, e.fp)
