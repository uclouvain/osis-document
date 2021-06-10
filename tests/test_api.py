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
from unittest import mock

from django.shortcuts import resolve_url
from django.test import override_settings
from django.utils.datetime_safe import datetime
from rest_framework.test import APITestCase

from base.tests.factories.user import UserFactory
from osis_document.enums import TokenAccess
from osis_document.tests.factories import PdfUploadFactory, WriteTokenFactory, ReadTokenFactory


@override_settings(ROOT_URLCONF="osis_document.tests.document_test.urls")
class APIViewsTestCase(APITestCase):
    def test_get_token(self):
        self.client.force_authenticate(UserFactory())
        response = self.client.post(resolve_url('api:get-token', pk=PdfUploadFactory().pk))
        self.assertEqual(response.status_code, 201)
        token = response.json()
        self.assertEqual(token['access'], TokenAccess.WRITE.name)

        response = self.client.post(resolve_url('api:get-token', pk=PdfUploadFactory().pk), {
            'access': TokenAccess.READ.name,
            'expires_at': datetime(2021, 6, 10)
        })
        self.assertEqual(response.status_code, 201)
        token = response.json()
        self.assertEqual(token['access'], TokenAccess.READ.name)
        self.assertEqual(token['expires_at'], "2021-06-10T00:00:00")

        response = self.client.post(resolve_url('api:get-token', pk='327b946a-4ee5-48a0-8403-c0b9e5dd84a3'))
        self.assertEqual(response.status_code, 404)

    def test_get_metadata(self):
        self.client.force_authenticate(UserFactory())
        response = self.client.get(resolve_url('api:get-metadata', pk=PdfUploadFactory().pk))
        self.assertEqual(response.status_code, 200)
        metadata = response.json()
        self.assertIn('mimetype', metadata)
        self.assertIn('md5', metadata)
        self.assertIn('name', metadata)

        response = self.client.get(resolve_url('api:get-metadata', pk='327b946a-4ee5-48a0-8403-c0b9e5dd84a3'))
        self.assertEqual(response.status_code, 404)

    def test_confirm_upload(self):
        self.client.force_authenticate(UserFactory())
        token = WriteTokenFactory()
        response = self.client.put(resolve_url('api:confirm-upload', token=token.token))
        self.assertEqual(200, response.status_code)
        json = response.json()
        self.assertIn('upload_id', json)

        response = self.client.put(resolve_url('api:confirm-upload', token='foobar'))
        self.assertEqual(404, response.status_code)

        token = ReadTokenFactory()
        response = self.client.put(resolve_url('api:confirm-upload', token=token.token))
        self.assertEqual(404, response.status_code)

        with mock.patch('django.utils.timezone.now', return_value=datetime(1990, 1, 1)):
            token = WriteTokenFactory()
        response = self.client.put(resolve_url('api:confirm-upload', token=token.token))
        self.assertEqual(404, response.status_code)
