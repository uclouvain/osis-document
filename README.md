TEST ci

# OSIS Document

`OSIS Document` is a Django application to manage document uploads across OSIS plateform.

# Requirements

`OSIS Document` requires

- Django 2.2+
- Django REST Framework 3.12+


# How to install ?

## For production

```bash
# From your osis install, with python environment activated
pip install git+https://github.com/uclouvain/osis-document.git@dev#egg=osis_document
```

## For development

```bash
# From your osis install, with python environment activated
git clone git@github.com:uclouvain/osis-document.git
pip install -e ./osis-document
```

## Configuring OSIS Document

Add `osis_document` to `INSTALLED_APPS` and configure the base url:

```python
import os

INSTALLED_APPS = (
    ...
    'osis_document',
    ...
)

# The primary server full url
OSIS_DOCUMENT_BASE_URL = os.environ.get('OSIS_DOCUMENT_BASE_URL', 'https://yourserver.com/osis_document/')
# The shared secret between servers
OSIS_DOCUMENT_API_SHARED_SECRET = os.environ.get('OSIS_DOCUMENT_API_SHARED_SECRET', 'change-this-secret')
# The request upload rate limit for a user, see https://www.django-rest-framework.org/api-guide/throttling/#setting-the-throttling-policy
OSIS_DOCUMENT_UPLOAD_LIMIT = '10/minute'
# When used on multiple servers, set the domains on which raw files may be displayed (for Content Security Policy)
OSIS_DOCUMENT_DOMAIN_LIST = [
    '127.0.0.1:8001',
]
```

OSIS-Document is aimed at being run on multiple servers, so on your primary server, add it to your `urls.py` 
matching what you set in `settings.OSIS_DOCUMENT_BASE_URL`:

```python
if 'osis_document' in settings.INSTALLED_APPS:
    urlpatterns += (path('osis_document/', include('osis_document.urls')), )
```


# Using OSIS Document

`osis_document` is used to decouple file upload handling and retrieving from Django forms and apps with an accent on user interface.

## Declaring a file field on a model

To declare a file field within a Django model :

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from osis_document.contrib import FileField

class MyModel(models.Model):
    files = FileField(
        verbose_name=_("ID card"),
        max_size=True,  # To restrict file size
        upload_button_text='',  # To customize dropzone button text
        upload_text='', # To customize dropzone text
        min_files=1,  # To require at least 1 file
        max_files=2,  # To require at most 2 files
        mimetypes=['application/pdf', 'image/png', 'image/jpeg'],
        can_edit_filename=False,  # To prevent filename editing
        automatic_upload=False,  # To force displaying upload button
    )
)
```

This `FileField` model field is associated with the form field `FileUploadField`, which can handle file upload on 
custom forms, even on a secondary server.

```python
from django.forms import forms
from osis_document.contrib import FileUploadField

class MyModelForm(forms.Form):
    files = FileUploadField()

    def save(self):
        uuids = self.fields['files'].persist(self.cleaned_data['files'])
```

Note 1: it is very important to call the persists method on the field upon saving, it returns the uuid of the files (it is your job to store these uuids).

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

To get raw info or download url given a file token:

```python
from osis_document.api.utils import get_remote_metadata
 
metadata = get_remote_metadata(token)
```

Available metadata info:

- `name`: The name of the file (as set by the uploader)
- `size`: The size of the file in bytes
- `mimetype`: The MIME type as per detected by python-magic
- `uploaded_at`: The datetime the file was uploaded at
- `md5`: The md5 checksum of the file
- `url`: The file url to get the file


# Contributing to OSIS-Document

## Frontend

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

## OpenAPI schema generation

To ease generation, use the provided generator:
```console
./manage.py generateschema --urlconf=osis_document.urls --generator_class osis_document.api.schema.OsisDocumentSchemaGenerator --file osis_document/schema.yml
```

# Communication between servers

To communicate between two servers (e.g., with SDK-based code), requests are sent with the header `X-Api-Key`
containing the shared secret set in the server using the setting `OSIS_DOCUMENT_API_SHARED_SECRET`, so make sure it set. 
