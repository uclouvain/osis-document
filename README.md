# OSIS Document

`OSIS Document` is a Django application to manage document uploads across OSIS plateform.

# Requirements

`OSIS Document` requires

- Django 3.2+
- Django REST Framework 3.12+
- Requests 2+


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
    ...,
    'osis_document',
    ...,
)

# The primary server full url
OSIS_DOCUMENT_BASE_URL = os.environ.get('OSIS_DOCUMENT_BASE_URL', 'https://yourserver.com/osis_document/')
# The shared secret between servers
OSIS_DOCUMENT_API_SHARED_SECRET = os.environ.get('OSIS_DOCUMENT_API_SHARED_SECRET', 'change-this-secret')
# The request upload rate limit for a user, see https://www.django-rest-framework.org/api-guide/throttling/#setting-the-throttling-policy
OSIS_DOCUMENT_UPLOAD_LIMIT = '10/minute'
# A token max age (in seconds) after which it may be no longer be used for viewing/modifying the corresponding upload
OSIS_DOCUMENT_TOKEN_MAX_AGE = 60 * 15
# A temporary upload max age (in seconds) after which it may be deleted by the celery task
OSIS_DOCUMENT_TEMP_UPLOAD_MAX_AGE = 60 * 15
# When used on multiple servers, set the domains on which raw files may be displayed (for Content Security Policy)
OSIS_DOCUMENT_DOMAIN_LIST = [
    '127.0.0.1:8001',
]
# To configure which extensions are allowed by default for any upload
OSIS_DOCUMENT_ALLOWED_EXTENSIONS = ['pdf', 'txt', 'docx', 'doc', 'odt', 'png', 'jpg']
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
        upload_to='',  # This attribute provides a way of setting the upload directory
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


### Specify the upload directory

You can specify the upload directory through the `upload_to` property.

When you use the `FileField` model field, the `upload_to` property can either be a string or a function:
- if it is a string, it is prepended to the file name. It may contain strftime() formatting, which will be replaced by the date/time of the file upload.
- if it is a function, it will be called to obtain the upload path, including the file name. This callable must accept two arguments:
  - the current instance of the model where the file field is defined;
  - the file name that was originally given to the file.

When you use the `FileUploadField` form field, you can specify the `upload_to` property as a string that will be prepended to the file name.
However, if you want to reuse the `upload_to` property defined in the related `FileField` model field, you need to specify the `related_model` property in the `FileUploadField` form field with the three following properties to identify the related model field:
- `field`: the name of the model field;
- `model`: the name of the model containing the previous field;
- `app`: the name of the application containing the previous model.

In addition, if the `upload_to` property is a function based on some instance attributes, you must also:
- add a 4th property to the `related_model` property:
  - `instance_filter_fields`: a list of field names that uniquely identify an instance (such as `["uuid"]`).
- Pass the model instance as a parameter to the `persist` function. The fields specified in the `instance_filter_fields` property must be accessible via this instance.

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
- `hash`: The sh256 hash of the file
- `url`: The file url to get the file

## Listening javascript events

Some javascript events are triggered by the `Uploader` component:

- `osisdocument:add` when a file has been uploaded.
- `osisdocument:delete` when a file has been removed.

The triggered event contains the tokens related to the uploader before the action (`event.detail.oldTokens`) and
after it (`event.detail.newTokens`) following this format:
```json
{
  "detail": {
     "oldTokens": {"1": "first_token", "2": "second_token"},
     "newTokens": {"1": "first_token", "2": "second_token", "3": "third_token"}
  }
}
```

Javascript example to listen these events:

```javascript
const uploader = document.getElementsByClassName('osis-document-uploader')[0];

uploader.addEventListener('osisdocument:add', event => {
    console.log('old tokens', event.detail.oldTokens);
    console.log('new tokens', event.detail.newTokens);
}, false);
```

Note that the `Uploader` component has the `osis-document-uploader` class.

## File format conversion

In order to use the file conversion `OSIS_UPLOAD_FOLDER` must be defined
in the `.env` file that shows the whole path to the folder of the
downloaded files in  OSIS-Document

### Converter use
Allowed Format : `Docx`, `Doc`, `Odt`, `txt`, `JPG`, and `PNG`

```python
from osis_document.contrib.post_processing.converteur.context import Context
from osis_document.contrib.post_processing.converteur.converteur_image_to_pdf import ConverterImageToPdf

context = Context(converteur=ConverterImageToPdf(), upload_object=Upload.objects.get(uuid=""))
context.make_conversion()
```
To convert a text file into a pdf use `ConverterTextDocumentToPdf`
instead of ConverterImageToPdf

## Files merge in PDF
In order to use the pdf merging `OSIS_UPLOAD_FOLDER` must be defined in
the `.env` file  that shows the whole path to the folder of the
downloaded files in  OSIS-Document and LibreOffice must be installed on
the computer.

If the files are not in the PDF format the correct conversion class must
be used before merging.

```python
from osis_document.contrib.post_processing.merge_file_to_pdf import merge_files_to_one_pdf

merge_files_to_one_pdf(liste_uuid_files=[], output_file_name='output.pdf')
```

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
