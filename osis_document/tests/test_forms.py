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
from unittest.mock import Mock, patch

from django import forms
from django.test import TestCase, override_settings
from osis_document.contrib.forms import FileUploadField, TokenField
from osis_document.tests.factories import WriteTokenFactory, PdfUploadFactory, ModifiedUploadFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class FormTestCase(TestCase):
    def setUp(self):
        self.mock_remote_metadata = patch(
            'osis_document.api.utils.get_remote_metadata',
            return_value={
                "size": 1024,
                "mimetype": "application/pdf",
                "name": "test.pdf",
                "url": "http://dummyurl.com/document/file/AZERTYIOOHGFDFGHJKLKJHG",
            },
        )
        self.mock_remote_metadata.start()
        self.addCleanup(self.mock_remote_metadata.stop)
        mock_remote_token = patch('osis_document.api.utils.get_remote_token', return_value='a:token')
        self.mock_remote_token = mock_remote_token.start()
        self.addCleanup(mock_remote_token.stop)

    def test_normal_behavior(self):
        class TestForm(forms.Form):
            media = FileUploadField()

        form = TestForm(
            {
                'media_0': WriteTokenFactory().token,
            }
        )
        self.assertTrue(form.is_valid(), msg=form.errors)

        form = TestForm(
            {
                'media': [WriteTokenFactory().token],
            }
        )
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_initial_uuid(self):
        class TestForm(forms.Form):
            media = FileUploadField()

        random_uuid = '8620708e-13fe-437d-9193-edb37e46055d'
        form = TestForm(
            initial={
                'media': [random_uuid],
            }
        )
        self.assertNotIn(random_uuid, form.as_p())
        self.mock_remote_token.assert_called()

    def test_initial_no_value(self):
        class TestForm(forms.Form):
            media = FileUploadField()

        TestForm(
            initial={
                'media': None,
            }
        ).as_p()
        self.mock_remote_token.assert_not_called()

    def test_initial_token(self):
        class TestForm(forms.Form):
            media = FileUploadField()

        TestForm(
            initial={
                'media': [WriteTokenFactory().token],
            }
        ).as_p()
        self.mock_remote_token.assert_not_called()
        TestForm().as_p()
        self.mock_remote_token.assert_not_called()

    def test_wrong_upload(self):
        class TestForm(forms.Form):
            media = FileUploadField()

        form = TestForm(
            {
                'media_0': 'foobar',
            }
        )

        with patch('osis_document.api.utils.get_remote_metadata') as get_remote_metadata:
            get_remote_metadata.return_value = None
            self.assertFalse(form.is_valid(), form.errors)
        error = TokenField.default_error_messages['nonexistent']
        self.assertIn(str(error), form.errors['media'][0])

    def test_data_not_a_list(self):
        class TestForm(forms.Form):
            media = FileUploadField()

        form = TestForm(
            {
                'media': WriteTokenFactory().token,
            }
        )

        with patch('osis_document.api.utils.get_remote_metadata') as get_remote_metadata:
            get_remote_metadata.return_value = None
            self.assertFalse(form.is_valid(), form.errors)
        error = forms.Field.default_error_messages['required']
        self.assertEqual(str(error), form.errors['media'][0])

    def test_check_file_min_count(self):
        class TestFormMin(forms.Form):
            media = FileUploadField(min_files=2)

        form = TestFormMin(
            {
                'media_0': WriteTokenFactory().token,
                'media_1': WriteTokenFactory().token,
            }
        )
        self.assertTrue(form.is_valid(), msg=form.errors)
        self.assertEqual(2, len(form.cleaned_data['media']))
        form = TestFormMin(
            {
                'media_0': WriteTokenFactory().token,
            }
        )
        self.assertFalse(form.is_valid())

    def test_check_file_max_count(self):
        class TestFormMax(forms.Form):
            media = FileUploadField(max_files=1)

        form = TestFormMax(
            {
                'media_0': WriteTokenFactory().token,
                'media_1': WriteTokenFactory().token,
            }
        )
        self.assertFalse(form.is_valid())
        form = TestFormMax(
            {
                'media_0': WriteTokenFactory().token,
            }
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(1, len(form.cleaned_data['media']))

    def test_check_file_min_max_count(self):
        class TestFormMinMax(forms.Form):
            media = FileUploadField(min_files=2, max_files=2)

        form = TestFormMinMax(
            {
                'media_0': WriteTokenFactory().token,
            }
        )
        self.assertFalse(form.is_valid())
        form = TestFormMinMax(
            {
                'media_0': WriteTokenFactory().token,
                'media_1': WriteTokenFactory().token,
                'media_2': WriteTokenFactory().token,
            }
        )
        self.assertFalse(form.is_valid())
        form = TestFormMinMax(
            {
                'media_0': WriteTokenFactory().token,
                'media_1': WriteTokenFactory().token,
            }
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(2, len(form.cleaned_data['media']))

    def test_check_max_size(self):
        class TestForm(forms.Form):
            media = FileUploadField(max_size=2)

        form = TestForm(
            {
                'media_0': WriteTokenFactory().token,
            }
        )
        self.assertFalse(form.is_valid(), form.errors)
        error = TokenField.default_error_messages['size']
        self.assertIn(str(error), form.errors['media'][0])

        # The max size is not defined in the settings
        with override_settings(OSIS_DOCUMENT_MAX_UPLOAD_SIZE=None):
            class TestForm(forms.Form):
                media_with_limited_size = FileUploadField(max_size=2)
                media_without_limited_size = FileUploadField()

            form = TestForm()

            self.assertEqual(form.fields['media_with_limited_size'].max_size, 2)
            self.assertEqual(form.fields['media_without_limited_size'].max_size, None)

        # The max size is defined in the settings
        with override_settings(OSIS_DOCUMENT_MAX_UPLOAD_SIZE=10):
            class TestForm(forms.Form):
                media_with_lower_limited_size = FileUploadField(max_size=2)
                media_with_greater_limited_size = FileUploadField(max_size=15)
                media_without_limited_size = FileUploadField()

            form = TestForm()

            self.assertEqual(form.fields['media_with_lower_limited_size'].max_size, 2)
            self.assertEqual(form.fields['media_with_greater_limited_size'].max_size, 10)
            self.assertEqual(form.fields['media_without_limited_size'].max_size, 10)

    def test_check_mimetype(self):
        class TestForm(forms.Form):
            media = FileUploadField(mimetypes=('image/jpeg',))

        form = TestForm(
            {
                'media_0': WriteTokenFactory().token,
            }
        )
        self.assertFalse(form.is_valid(), form.errors)
        error = TokenField.default_error_messages['mimetype']
        self.assertIn(str(error), form.errors['media'][0])

    def test_persist_confirms_token(self):
        class TestForm(forms.Form):
            media = FileUploadField(
                related_model={
                    'app': 'app_name',
                    'model': 'model_name',
                    'field': 'field_name',
                    'instance_filter_fields': ['id'],
                }
            )

        mock_instance = Mock(id=10)
        token = WriteTokenFactory().token
        form = TestForm({'media_0': token})
        self.assertTrue(form.is_valid(), msg=form.errors)
        with patch('osis_document.api.utils.confirm_remote_upload') as confirm_remote_upload:
            confirm_remote_upload.return_value = {"uuid": "something"}
            confirmed_ids = form.fields['media'].persist(form.cleaned_data['media'], mock_instance)
            self.assertListEqual(confirmed_ids, [{"uuid": "something"}])

    def test_check_disabled_field(self):
        class TestForm(forms.Form):
            media = FileUploadField(disabled=True, required=False)

        # Without initial data: [] -> []
        form = TestForm(
            data={
                'media_0': WriteTokenFactory().token,
            }
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data.get('media'), [])

        # With initial data: [uuid] -> [token]
        form = TestForm(
            data={
                'media_0': WriteTokenFactory().token,
            },
            initial={'media': [str(uuid.uuid4())]},
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data.get('media'), ['a:token'])


    @patch('osis_document.api.utils.get_remote_token')
    def test_for_modified_upload(self, get_remote_token):
        get_remote_token.return_value = 'a:token'

        class TestFormWithModifiedUpload(forms.Form):
            media = FileUploadField(for_modified_upload=True)

        upload = PdfUploadFactory()
        modified_upload = ModifiedUploadFactory(upload=upload)

        form = TestFormWithModifiedUpload(
            initial={
                'media': [upload.uuid],
            },
        )

        form.as_p()

        get_remote_token.assert_called_once_with(
            upload.uuid,
            write_token=True,
            for_modified_upload=True,
        )

        get_remote_token.reset_mock()

        class TestFormWithoutModifiedUpload(forms.Form):
            media = FileUploadField()

        form = TestFormWithoutModifiedUpload(
            initial={
                'media': [upload.uuid],
            },
        )

        form.as_p()

        get_remote_token.assert_called_once_with(
            upload.uuid,
            write_token=True,
            for_modified_upload=False,
        )
