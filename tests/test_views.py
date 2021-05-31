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
from datetime import datetime

from django.core.files.base import ContentFile
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings

from osis_document.enums import FileStatus, TokenAccess
from osis_document.models import Upload, Token
from osis_document.tests.factories import WriteTokenFactory, ReadTokenFactory


@override_settings(ROOT_URLCONF='osis_document.contrib.urls')
class RequestUploadTestCase(TestCase):
    def test_request_upload_without_file(self):
        response = self.client.post(resolve_url('request-upload'), {})
        self.assertEqual(400, response.status_code)

    def test_upload(self):
        file = ContentFile(b'hello world', 'foo.pdf')
        form_data = {'file': file}

        self.assertFalse(Upload.objects.exists())

        response = self.client.post(resolve_url('request-upload'), form_data)
        json = response.json()
        self.assertIn('token', json)
        self.assertTrue(Upload.objects.exists())
        self.assertTrue(Token.objects.exists())
        self.assertEqual(Upload.objects.first().status, FileStatus.REQUESTED.name)
        self.assertTrue(Token.objects.first().access, TokenAccess.WRITE.name)

    def test_confirm(self):
        token = WriteTokenFactory()
        response = self.client.post(resolve_url('confirm-upload', token=token.token))
        json = response.json()
        self.assertIn('uuid', json)

    def test_confirm_non_existent(self):
        response = self.client.post(resolve_url('confirm-upload', token='foobar'))
        self.assertEqual(400, response.status_code)

    def test_confirm_read_token(self):
        token = ReadTokenFactory()
        response = self.client.post(resolve_url('confirm-upload', token=token.token))
        self.assertEqual(400, response.status_code)

    def test_confirm_upload_too_old(self):
        token = WriteTokenFactory(created_at=datetime(1990, 1, 1))
        response = self.client.post(resolve_url('confirm-upload', token=token.token))
        self.assertEqual(400, response.status_code)
