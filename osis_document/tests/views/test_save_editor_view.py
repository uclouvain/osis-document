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

from django.core.files.base import ContentFile
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings

from osis_document.models import Upload
from osis_document.tests.factories import PdfUploadFactory, ReadTokenFactory, WriteTokenFactory

SMALLEST_PDF = b"""%PDF-1.
1 0 obj<</Pages 2 0 R>>endobj 2 0 obj<</Kids[3 0 R]/Count 1>>endobj 3 0 obj<</MediaBox[0 0 612 792]>>endobj trailer<</Root 1 0 R>>"""


@override_settings(ROOT_URLCONF="osis_document.urls", OSIS_DOCUMENT_API_SHARED_SECRET='foobar')
class SaveEditorViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.upload = PdfUploadFactory()
        cls.file = ContentFile(SMALLEST_PDF, 'foo.pdf')

    def setUp(self):
        self.client.defaults = {'HTTP_X_API_KEY': 'foobar'}

    def test_post_original_with_read_token(self):
        token = ReadTokenFactory(upload=self.upload)
        url = resolve_url('save-editor', token=token.token)
        response = self.client.post(url, {'file': self.file, 'rotations': '{}'})
        self.assertEqual(404, response.status_code)

    def test_post_original(self):
        token = WriteTokenFactory(upload=self.upload)
        url = resolve_url('save-editor', token=token.token)
        response = self.client.post(url, {'file': self.file, 'rotations': '{}'})
        self.assertEqual(200, response.status_code)
        self.upload.refresh_from_db()
        self.assertEqual(self.upload.file.read(), SMALLEST_PDF)
        with self.assertRaises(Upload.modified_upload.RelatedObjectDoesNotExist):
            self.upload.modified_upload

    def test_post_modified(self):
        token = WriteTokenFactory(upload=self.upload, for_modified_upload=True)
        url = resolve_url('save-editor', token=token.token)
        response = self.client.post(url, {'file': self.file, 'rotations': '{}'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(self.upload.file.read(), b'hello world')
        self.assertEqual(self.upload.modified_upload.file.read(), SMALLEST_PDF)
