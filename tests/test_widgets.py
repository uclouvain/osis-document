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
import uuid

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from osis_document.contrib.widgets import FileUploadWidget


@override_settings(
    ROOT_URLCONF='osis_document.tests.document_test.urls',
    OSIS_DOCUMENT_BASE_URL='/document/',
)
class WidgetTestCase(TestCase):
    def test_widget_is_uuid(self):
        widget = FileUploadWidget(size=2)
        stub_uuid = uuid.uuid4()
        render = widget.render('foo', [stub_uuid])
        self.assertIn(str(stub_uuid), render)

        stub_uuid2 = uuid.uuid4()
        render = widget.render('foo', [stub_uuid, stub_uuid2])
        self.assertIn(str(stub_uuid), render)
        self.assertIn(str(stub_uuid2), render)

    def test_widget_renders_attributes(self):
        widget = FileUploadWidget(size=1, mimetypes=['application/pdf'])
        render = widget.render('foo', [])
        self.assertIn('application/pdf', render)

        widget = FileUploadWidget(size=1, max_size=1024)
        render = widget.render('foo', [])
        self.assertIn('1024', render)
        self.assertNotIn('automatic', render)

        widget = FileUploadWidget(size=1, automatic_upload=False)
        render = widget.render('foo', [])
        self.assertIn('automatic', render)

    @override_settings(OSIS_DOCUMENT_BASE_URL=None)
    def test_widget_raise_exception_missing_upload_url(self):
        widget = FileUploadWidget(size=1)
        with self.assertRaises(ImproperlyConfigured):
            widget.render('foo', [])
