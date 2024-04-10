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
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from osis_document.contrib.widgets import FileUploadWidget
from osis_document.tests.factories import PdfUploadFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='/document/')
class WidgetTestCase(TestCase):
    def test_widget_with_no_value(self):
        widget = FileUploadWidget(size=2)
        render = widget.render('foo', None)
        self.assertNotIn('data-values', render)

    @patch('osis_document.api.utils.get_remote_token')
    def test_widget_should_not_expose_uuid(self, mock_remote_token):
        mock_remote_token.return_value = 'some:token'
        widget = FileUploadWidget(size=2)
        stub_uuid = PdfUploadFactory().uuid
        render = widget.render('foo', [stub_uuid])
        self.assertNotIn(str(stub_uuid), render)
        self.assertIn('data-values="some:token"', render)
        mock_remote_token.assert_called_once_with(
            stub_uuid,
            write_token=True,
            for_modified_upload=False,
        )

    @patch('osis_document.api.utils.get_remote_token')
    def test_widget_with_modified_upload(self, mock_remote_token):
        mock_remote_token.return_value = 'some:token'
        widget = FileUploadWidget(size=2, for_modified_upload=True)
        stub_uuid = PdfUploadFactory().uuid
        widget.render('foo', [stub_uuid])
        mock_remote_token.assert_called_once_with(
            stub_uuid,
            write_token=True,
            for_modified_upload=True,
        )

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

        widget = FileUploadWidget(can_edit_filename=False)
        render = widget.render('foo', [])
        self.assertIn('data-editable-filename="false"', render)

        widget = FileUploadWidget(upload_text="foo", upload_button_text="bar")
        render = widget.render('foo', [])
        self.assertIn('data-upload-text="foo"', render)
        self.assertIn('data-upload-button-text="bar"', render)

        widget = FileUploadWidget(min_files=2, max_files=4)
        render = widget.render('foo', [])
        self.assertIn('data-min-files="2"', render)
        self.assertIn('data-max-files="4"', render)

    @override_settings(OSIS_DOCUMENT_BASE_URL=None)
    def test_widget_raise_exception_missing_upload_url(self):
        widget = FileUploadWidget(size=1)
        with self.assertRaises(ImproperlyConfigured):
            widget.render('foo', [])
