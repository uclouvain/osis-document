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

from osis_document.tests.factories import PdfUploadFactory


@override_settings(ROOT_URLCONF="osis_document.urls", OSIS_DOCUMENT_API_SHARED_SECRET='foobar')
class DeclareFileInfectedViewTestCase(APITestCase):
    def setUp(self):
        self.client.defaults = {'HTTP_X_API_KEY': 'foobar'}
        self.infected_file = PdfUploadFactory()
        self.infected_filepath = str(self.infected_file.file)
        self.url = resolve_url('declare-file-as-infected')

    def test_protected(self):
        self.client.defaults = {}
        response = self.client.post(self.url, {'path': self.infected_filepath})
        self.assertEqual(403, response.status_code)

    def test_declare_as_infected(self):
        response = self.client.post(self.url, {'path': self.infected_filepath})
        self.assertEqual(202, response.status_code)
        self.assertIn('uuid', response.json())

    def test_confirm_upload_with_unknown_path(self):
        response = self.client.post(self.url, {'path': 'foobar'})
        self.assertEqual(400, response.status_code)
