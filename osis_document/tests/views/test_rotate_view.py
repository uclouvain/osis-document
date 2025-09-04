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

from osis_document.tests.factories import ImageUploadFactory, ReadTokenFactory, WriteTokenFactory


@override_settings(ROOT_URLCONF='osis_document.urls', OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class RotateViewTestCase(APITestCase):
    def test_write_only(self):
        token = ReadTokenFactory()
        response = self.client.post(resolve_url('rotate-image', token=token.token))
        self.assertEqual(response.status_code, 404)

    def test_image_only(self):
        token = WriteTokenFactory()
        response = self.client.post(resolve_url('rotate-image', token=token.token))
        self.assertEqual(response.status_code, 400)

    def test_successfully_rotates(self):
        token = WriteTokenFactory(upload=ImageUploadFactory())
        response = self.client.post(resolve_url('rotate-image', token=token.token))
        self.assertNotEqual(response.json()['token'], token.token)
        self.assertEqual(response.status_code, 200)
