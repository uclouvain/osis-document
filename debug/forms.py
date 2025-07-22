from django import forms

from contrib import FileUploadField


class SingleFileUploadForm(forms.Form):
    file = FileUploadField(max_files=1)


class MultipleFileUploadForm(forms.Form):
    files = FileUploadField()
