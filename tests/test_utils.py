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
from unittest import mock

from django.test import TestCase, override_settings

from osis_document.exceptions import Md5Mismatch
from osis_document.tests.factories import WriteTokenFactory
from osis_document.utils import get_metadata, save_raw_upload


@override_settings(ROOT_URLCONF='osis_document.tests.document_test.urls',
                   OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class MetadataTestCase(TestCase):
    def test_with_token(self):
        token = WriteTokenFactory()
        metadata = get_metadata(token.token)
        self.assertEqual(metadata['size'], 1024)
        self.assertEqual(metadata['mimetype'], 'application/pdf')
        self.assertEqual(metadata['md5'], '5eb63bbbe01eeed093cb22bb8f5acdc3')
        self.assertIn('url', metadata)

        with mock.patch('django.utils.timezone.now', return_value=datetime(1990, 1, 1)):
            old_token = WriteTokenFactory(upload=token.upload)
            self.assertIsNone(get_metadata(old_token.token))

    def test_bad_md5(self):
        token = WriteTokenFactory(upload__metadata={'md5': 'badvalue'})
        with self.assertRaises(Md5Mismatch):
            get_metadata(token.token)


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class RawUploadTestCase(TestCase):
    def test_with_bytes(self):
        token = save_raw_upload(
            file=bytes('my file content', encoding='utf8'),
            name='my_file_name.txt',
            mimetype='text/plain',
        )
        metadata = get_metadata(token.token)
        self.assertEqual(metadata['size'], 48)
        self.assertEqual(metadata['mimetype'], 'text/plain')
        self.assertEqual(metadata['md5'], 'ebf9d9524ad7f702a2c3a75f060024f1')
