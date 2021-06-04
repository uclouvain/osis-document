# OSIS Document

`OSIS Document` is a Django application to manage document uploads across OSIS plateform.

# Requirements

`OSIS Document` requires

- Django 2.2+
- Django REST Framework 3.12+
- python-magic 0.4.22+
- Vue 3 (with teleport)


# How to install ?

## Configuring Django

Add `osis_document` to `INSTALLED_APPS` and configure the base url:

```python
INSTALLED_APPS = (
    ...
    'osis_document',
    ...
)

OSIS_DOCUMENT_BASE_URL = getenv('OSIS_DOCUMENT_BASE_URL', '/osis-document/')
```


# Using OSIS Document

`osis_document` is used to decouple file upload handling and retrieving from Django forms and apps with an accent on user interface.

## Declaring a file field

To declare a file field within a Django model :

```python

from django.db import models
from osis_document import FileField

class MyModel(models.Model):
    files = FileField(
        verbose_name=_("ID card"),
        max_files=2,
        mimetypes=['application/pdf', 'image/png', 'image/jpeg'],
    )
)
```

This `FileField` model field is associated with the form field `FileUploadField` , which can handle file upload on custom forms.

```python
from django.forms import forms
from osis_document import FileUploadField

class MyModelForm(forms.Form):
    files = FileUploadField(
        verbose_name=_("ID card"),
        max_files=2,
        mimetypes=['application/pdf', 'image/png', 'image/jpeg'],
    )

    def save(self):
        uuids = self.files.persist(self.cleaned_data['files'])
```

Note 1: it is very important to call the persists method on the field upon saving, it return the uuid of the files (it is your job to store these uuids).

Note 2: you can pick examples of MIME types from [this list](<https://developer.mozilla.org/fr/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types>).

## Rendering an uploaded file in a template

To work with uploaded files in templates :

```html
{% load osis_document %}
<ul>
{% for file_uuid in my_instance.files %}
    {% get_metadata file_uuid as metadata %}
    {% get_file_url file_uuid as file_url %}
    <li>
        <a href="{{ file_url }}">
            {{ metadata.name }} ({{ metadata.mimetype }} - {{ metadata.size|filesizeformat }})
        </a>
    </li>
{% endfor %}
</ul>
```

See next section on what information is available in the metadata.

## Getting info about an uploaded file

To get raw info or download url given a file uuid:

```python
from osis_document import get_metadata, get_download_url
 
metadata = get_metadata(uuid)
download_url = get_download_url(uuid)
```

Available metadata info:

- `name`: The name of the file (as set by the uploader)
- `size`: The size of the file in bytes
- `mimetype`: The MIME type as per detected by python-magic
- `uploaded_at`: The datetime the file was uploaded at


# Contributing to OSIS-History

To contribute to the frontend part of this module, install `npm` > 6 (included in [https://nodejs.org/en/download/](nodejs)), and run:
```console
cd osis_document
npm clean-install
npm run build
```

Commands available:
 - `npm run build` builds the frontend component to `osis_document/static/osis_document`
 - `npm run watch` builds the frontend component to `osis_document/static/osis_document` and watch for file changes (warning: this not a hot-reload, you have to refresh your page)
 - `npm run storybook` serve user stories page for development
 - `npm run lint` checks Javascript syntax
 - `npm run test` launch tests
 - `npm run coverage` launch tests with coverage
