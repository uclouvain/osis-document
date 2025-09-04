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

from django.test import TestCase

from osis_document.models import Upload
from osis_document.tests.factories import PdfUploadFactory, ModifiedUploadFactory


class UploadTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pdf_upload_without_modified = PdfUploadFactory()
        cls.modified_upload = ModifiedUploadFactory()

    def test_assert_hash(self):
        with self.assertRaises(AssertionError):
            Upload.objects.create(size=1024)
        Upload.objects.create(
            size=1024,
            metadata={
                'hash': 'something',
            },
        )

    def test_get_file(self):
        with self.subTest('without modified modified=False'):
            self.assertEqual(
                self.pdf_upload_without_modified.get_file(),
                self.pdf_upload_without_modified.file,
            )
        with self.subTest('with modified modified=False'):
            self.assertEqual(
                self.modified_upload.upload.get_file(),
                self.modified_upload.upload.file,
            )
        with self.subTest('without modified modified=True'):
            self.assertEqual(
                self.pdf_upload_without_modified.get_file(modified=True),
                self.pdf_upload_without_modified.file,
            )
        with self.subTest('with modified modified=True'):
            self.assertEqual(
                self.modified_upload.upload.get_file(modified=True),
                self.modified_upload.file,
            )

    def test_get_hash(self):
        with self.subTest('without modified modified=False'):
            self.assertEqual(
                self.pdf_upload_without_modified.get_hash(),
                self.pdf_upload_without_modified.metadata['hash'],
            )
        with self.subTest('with modified modified=False'):
            self.assertEqual(
                self.modified_upload.upload.get_hash(),
                self.modified_upload.upload.metadata['hash'],
            )
        with self.subTest('without modified modified=True'):
            self.assertEqual(
                self.pdf_upload_without_modified.get_hash(modified=True),
                self.pdf_upload_without_modified.metadata['hash'],
            )
        with self.subTest('with modified modified=True'):
            self.assertEqual(
                self.modified_upload.upload.get_hash(modified=True),
                self.modified_upload.upload.metadata['modified_hash'],
            )
