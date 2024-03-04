# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest import mock

from django.shortcuts import resolve_url
from django.test import override_settings
from django.utils.datetime_safe import datetime
from rest_framework.test import APITestCase

from osis_document.models import Upload
from osis_document.tests.document_test.models import TestDocument
from osis_document.tests.factories import ReadTokenFactory, WriteTokenFactory


@override_settings(ROOT_URLCONF="osis_document.urls", OSIS_DOCUMENT_API_SHARED_SECRET='foobar')
class ConfirmUploadViewTestCase(APITestCase):
    def setUp(self):
        self.client.defaults = {'HTTP_X_API_KEY': 'foobar'}

    def test_protected(self):
        self.client.defaults = {}
        token = WriteTokenFactory()
        response = self.client.post(resolve_url('confirm-upload', token=token.token))
        self.assertEqual(403, response.status_code)

    def test_confirm_upload(self):
        token = WriteTokenFactory()
        response = self.client.post(resolve_url('confirm-upload', token=token.token))
        self.assertEqual(201, response.status_code)
        json = response.json()
        self.assertIn('uuid', json)

    def test_confirm_upload_with_upload_to(self):
        token = WriteTokenFactory()
        original_upload = token.upload
        response = self.client.post(
            resolve_url('confirm-upload', token=token.token),
            data={
                'upload_to': 'custom-path/',
            },
        )
        self.assertEqual(201, response.status_code)
        json = response.json()
        self.assertIn('uuid', json)
        confirmed_upload = Upload.objects.get(uuid=json['uuid'])
        self.assertNotEqual(original_upload.file.name, confirmed_upload.file.name)
        # The file has been uploaded in the directory that we explicitly specified
        self.assertRegex(confirmed_upload.file.name, r'custom-path/')

    def test_confirm_upload_with_related_model_and_string_upload_to(self):
        token = WriteTokenFactory()
        original_upload = token.upload
        response = self.client.post(
            resolve_url('confirm-upload', token=token.token),
            data={
                'related_model': {
                    'app': TestDocument._meta.app_label,
                    'model': 'TestDocument',
                    'field': 'documents',
                },
            },
        )
        self.assertEqual(201, response.status_code)
        json = response.json()
        self.assertIn('uuid', json)
        confirmed_upload = Upload.objects.get(uuid=json['uuid'])
        self.assertNotEqual(original_upload.file.name, confirmed_upload.file.name)
        # The file has been uploaded in the directory that we specified at the field level
        self.assertRegex(confirmed_upload.file.name, r'path/')

    def test_confirm_upload_with_related_model_and_callable_upload_to(self):
        token = WriteTokenFactory()
        original_upload = token.upload
        response = self.client.post(
            resolve_url('confirm-upload', token=token.token),
            data={
                'related_model': {
                    'app': TestDocument._meta.app_label,
                    'model': 'TestDocument',
                    'field': 'other_documents',
                },
            },
        )
        self.assertEqual(201, response.status_code)
        json = response.json()
        self.assertIn('uuid', json)
        confirmed_upload = Upload.objects.get(uuid=json['uuid'])
        self.assertNotEqual(original_upload.file.name, confirmed_upload.file.name)
        # The file has been uploaded in the directory that we specified at the field level
        self.assertRegex(confirmed_upload.file.name, r'default_path/others/')

    def test_confirm_upload_with_related_model_and_callable_upload_to_based_on_instance(self):
        doc_pk = TestDocument.objects.create(documents=[WriteTokenFactory().upload_id]).pk
        token = WriteTokenFactory()
        original_upload = token.upload
        response = self.client.post(
            resolve_url('confirm-upload', token=token.token),
            data={
                'related_model': {
                    'app': TestDocument._meta.app_label,
                    'model': 'TestDocument',
                    'field': 'other_documents',
                    'instance_filters': {
                        'pk': doc_pk,
                    },
                },
            },
        )
        self.assertEqual(201, response.status_code)
        json = response.json()
        self.assertIn('uuid', json)
        confirmed_upload = Upload.objects.get(uuid=json['uuid'])
        self.assertNotEqual(original_upload.file.name, confirmed_upload.file.name)
        # The file has been uploaded in the directory that we specified at the field level
        self.assertRegex(confirmed_upload.file.name, r'default_path/{}/'.format(doc_pk))

    def test_confirm_upload_with_unknown_related_model(self):
        token = WriteTokenFactory()
        response = self.client.post(
            resolve_url('confirm-upload', token=token.token),
            data={
                'related_model': {
                    'app': 'unknown_app',
                    'model': 'unknown_model',
                },
            },
        )
        self.assertEqual(400, response.status_code)
        self.assertTrue('related_model' in response.json())
        self.assertTrue('unknown_app:unknown_model' in response.json()['related_model'][0])

    def test_confirm_upload_with_unknown_related_model_field(self):
        token = WriteTokenFactory()
        response = self.client.post(
            resolve_url('confirm-upload', token=token.token),
            data={
                'related_model': {
                    'app': TestDocument._meta.app_label,
                    'model': 'TestDocument',
                    'field': 'unknown_field',
                },
            },
        )
        self.assertEqual(400, response.status_code)
        self.assertTrue('related_model' in response.json())
        self.assertTrue('unknown_field' in response.json()['related_model'][0])

    def test_confirm_upload_with_unknown_instance_filters(self):
        token = WriteTokenFactory()
        response = self.client.post(
            resolve_url('confirm-upload', token=token.token),
            data={
                'related_model': {
                    'app': TestDocument._meta.app_label,
                    'model': 'TestDocument',
                    'field': 'other_documents',
                    'instance_filters': {
                        'unknown_filter': '',
                    },
                },
            },
        )
        self.assertEqual(400, response.status_code)
        self.assertTrue('related_model' in response.json())
        self.assertTrue('unknown field' in response.json()['related_model'][0])

    def test_confirm_upload_with_unknown_instance(self):
        token = WriteTokenFactory()
        response = self.client.post(
            resolve_url('confirm-upload', token=token.token),
            data={
                'related_model': {
                    'app': TestDocument._meta.app_label,
                    'model': 'TestDocument',
                    'field': 'other_documents',
                    'instance_filters': {
                        'pk': -1,
                    },
                },
            },
        )
        self.assertEqual(400, response.status_code)
        self.assertTrue('related_model' in response.json())
        self.assertTrue('Impossible to find one single object' in response.json()['related_model'][0])

    def test_bad_token(self):
        response = self.client.post(resolve_url('confirm-upload', token='foobar'))
        self.assertEqual(400, response.status_code)

    def test_read_token(self):
        token = ReadTokenFactory()
        response = self.client.post(resolve_url('confirm-upload', token=token.token))
        self.assertEqual(400, response.status_code)

    def test_old_token(self):
        with mock.patch('django.utils.timezone.now', return_value=datetime(1990, 1, 1)):
            token = WriteTokenFactory()
        response = self.client.post(resolve_url('confirm-upload', token=token.token))
        self.assertEqual(400, response.status_code)
