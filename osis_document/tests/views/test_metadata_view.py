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

from django.shortcuts import resolve_url
from django.test import override_settings
from rest_framework.test import APITestCase

from osis_document.enums import DocumentError
from osis_document.tests import QueriesAssertionsMixin
from osis_document.tests.factories import ReadTokenFactory, WriteTokenFactory


@override_settings(ROOT_URLCONF='osis_document.urls', OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class MetadataViewTestCase(APITestCase):
    def test_get_metadata(self):
        token = ReadTokenFactory()
        response = self.client.get(resolve_url('get-metadata', token=token.token))
        self.assertEqual(response.status_code, 200)
        metadata = response.json()
        self.assertIn('mimetype', metadata)
        self.assertIn('hash', metadata)
        self.assertIn('name', metadata)
        self.assertIn('uploaded_at', metadata)

    def test_get_file_bad_token(self):
        response = self.client.get(resolve_url('get-metadata', token='token'))
        self.assertEqual(response.status_code, 404)

    def test_bad_hash(self):
        token = ReadTokenFactory(upload__metadata={'hash': 'badvalue'})
        response = self.client.get(resolve_url('get-metadata', token=token.token))
        self.assertEqual(response.status_code, 409)

    def test_change_metadata_read_only(self):
        token = ReadTokenFactory()
        response = self.client.post(resolve_url('change-metadata', token=token.token))
        self.assertEqual(response.status_code, 404)

    def test_change_metadata(self):
        token = WriteTokenFactory()
        response = self.client.post(
            resolve_url('change-metadata', token=token.token),
            {'name': 'foobar', 'new_property': 'value'},
        )
        self.assertEqual(response.status_code, 200)
        upload = token.upload
        upload.refresh_from_db()
        self.assertEqual(upload.metadata['name'], 'foobar')
        self.assertEqual(upload.metadata['new_property'], 'value')

    def test_change_metadata_hash_is_forbidden(self):
        token = WriteTokenFactory()
        original_hash = token.upload.metadata['hash']
        response = self.client.post(
            resolve_url('change-metadata', token=token.token),
            {
                'name': 'foobar',
                'hash': 'new_hash',
            },
        )
        self.assertEqual(response.status_code, 403)
        upload = token.upload
        upload.refresh_from_db()
        self.assertEqual(upload.metadata['hash'], original_hash)


@override_settings(ROOT_URLCONF='osis_document.urls', OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class MetadataListViewTestCase(QueriesAssertionsMixin, APITestCase):
    def test_get_metadata(self):
        tokens = [ReadTokenFactory().token, ReadTokenFactory().token]
        with self.assertNumQueriesLessThan(4):
            response = self.client.post(resolve_url('get-several-metadata'), data=tokens)
        self.assertEqual(response.status_code, 200)
        metadata = response.json()
        self.assertEqual(len(metadata), 2)
        for token in tokens:
            self.assertIn('mimetype', metadata[token])
            self.assertIn('hash', metadata[token])
            self.assertIn('name', metadata[token])
            self.assertIn('uploaded_at', metadata[token])

    def test_get_file_bad_token(self):
        tokens = ['bad-token']
        response = self.client.post(resolve_url('get-several-metadata'), data=tokens)
        self.assertEqual(response.status_code, 200)
        metadata = response.json()
        self.assertEqual(len(metadata), 1)
        self.assertIn('error', metadata[tokens[0]])
        self.assertEqual(metadata[tokens[0]]['error']['code'], DocumentError.TOKEN_NOT_FOUND.name)
        self.assertEqual(metadata[tokens[0]]['error']['message'], DocumentError.TOKEN_NOT_FOUND.value)
