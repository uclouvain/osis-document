# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from pathlib import Path

from django.core.files.base import ContentFile, File
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings

from osis_document.enums import FileStatus, TokenAccess
from osis_document.models import Token, Upload

SMALLEST_PDF = b"""%PDF-1.
1 0 obj<</Pages 2 0 R>>endobj 2 0 obj<</Kids[3 0 R]/Count 1>>endobj 3 0 obj<</MediaBox[0 0 612 792]>>endobj trailer<</Root 1 0 R>>"""


@override_settings(ROOT_URLCONF='osis_document.urls')
class RequestUploadViewTestCase(TestCase):
    def test_request_upload_without_file(self):
        response = self.client.post(resolve_url('request-upload'), {})
        self.assertEqual(400, response.status_code)

    @override_settings(OSIS_DOCUMENT_ALLOWED_EXTENSIONS=['txt'])
    def test_request_upload_with_bad_extension(self):
        file = ContentFile(SMALLEST_PDF, 'foo.pdf')
        response = self.client.post(resolve_url('request-upload'), {'file': file})
        self.assertEqual(400, response.status_code)

    @override_settings(ENABLE_MIMETYPE_VALIDATION=True)
    def test_request_upload_with_mime_smuggling(self):
        file = ContentFile(SMALLEST_PDF, 'foo.doc')
        response = self.client.post(resolve_url('request-upload'), {'file': file})
        self.assertEqual(409, response.status_code)

    def test_request_upload_with_docx(self):
        with (Path(__file__).parent.parent / 'test.docx').open('rb') as f:
            file = File(f, 'test.docx')
            response = self.client.post(resolve_url('request-upload'), {'file': file})
        self.assertEqual(201, response.status_code)

    def test_upload(self):
        file = ContentFile(SMALLEST_PDF, 'foo.pdf')
        self.assertFalse(Upload.objects.exists())

        response = self.client.post(resolve_url('request-upload'), {'file': file})
        json = response.json()
        self.assertIn('token', json)
        self.assertTrue(Upload.objects.exists())
        self.assertTrue(Token.objects.exists())
        self.assertEqual(Upload.objects.first().status, FileStatus.REQUESTED.name)
        self.assertTrue(Token.objects.first().access, TokenAccess.WRITE.name)

    def test_upload_long_filename(self):
        file = ContentFile(SMALLEST_PDF, 'a' * 300 + '.pdf')
        self.assertFalse(Upload.objects.exists())

        response = self.client.post(resolve_url('request-upload'), {'file': file})
        json = response.json()
        self.assertIn('token', json)
        self.assertTrue(Upload.objects.exists())
        self.assertTrue(Token.objects.exists())
        self.assertEqual(Upload.objects.first().status, FileStatus.REQUESTED.name)
        self.assertTrue(Token.objects.first().access, TokenAccess.WRITE.name)

    @override_settings(OSIS_DOCUMENT_DOMAIN_LIST=['http://dummyurl.com/'])
    def test_cors(self):
        file = ContentFile(SMALLEST_PDF, 'foo.pdf')
        response = self.client.post(resolve_url('request-upload'), {'file': file}, HTTP_ORIGIN="http://dummyurl.com/")
        self.assertTrue(response.has_header("Access-Control-Allow-Origin"))
        response = self.client.post(resolve_url('request-upload'), {'file': file}, HTTP_ORIGIN="http://wrongurl.com/")
        self.assertFalse(response.has_header("Access-Control-Allow-Origin"))
