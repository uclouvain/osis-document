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
from unittest.mock import patch

from django import forms

from django.test import TestCase, override_settings

from osis_document.contrib.forms import FileUploadField, TokenField
from osis_document.tests.factories import WriteTokenFactory


@override_settings(ROOT_URLCONF='osis_document.tests.document_test.urls',
                   OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class FormTestCase(TestCase):
    def test_normal_behavior(self):
        class TestForm(forms.Form):
            media = FileUploadField()

        form = TestForm({
            'media_0': WriteTokenFactory().token,
        })
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_wrong_upload(self):
        class TestForm(forms.Form):
            media = FileUploadField()

        form = TestForm({
            'media_0': 'foobar',
        })
        self.assertFalse(form.is_valid(), form.errors)
        error = TokenField.default_error_messages['nonexistent']
        self.assertIn(str(error), form.errors['media'][0])

    def test_check_limit(self):
        class TestForm(forms.Form):
            media = FileUploadField(limit=1)

        form = TestForm({
            'media_0': WriteTokenFactory().token,
            'media_1': uuid.uuid4(),
        })
        self.assertTrue(form.is_valid(), msg=form.errors)
        self.assertEqual(1, len(form.cleaned_data['media']))

    def test_check_max_size(self):
        class TestForm(forms.Form):
            media = FileUploadField(max_size=2)

        form = TestForm({
            'media_0': WriteTokenFactory().token,
        })
        self.assertFalse(form.is_valid(), form.errors)
        error = TokenField.default_error_messages['size']
        self.assertIn(str(error), form.errors['media'][0])

    def test_check_mimetype(self):
        class TestForm(forms.Form):
            media = FileUploadField(mimetypes=('image/jpeg',))

        form = TestForm({
            'media_0': WriteTokenFactory().token,
        })
        self.assertFalse(form.is_valid(), form.errors)
        error = TokenField.default_error_messages['mimetype']
        self.assertIn(str(error), form.errors['media'][0])

    def test_persist_confirms_token(self):
        class TestForm(forms.Form):
            media = FileUploadField()

        token = WriteTokenFactory().token
        form = TestForm({'media_0': token})
        self.assertTrue(form.is_valid(), msg=form.errors)
        with patch('osis_document.utils.confirm_upload') as confirm:
            form.fields['media'].persist(form.cleaned_data['media'])
            confirm.assert_called_with(token)
