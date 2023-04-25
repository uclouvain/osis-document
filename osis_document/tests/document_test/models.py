from django.db import models

from osis_document.contrib.fields import FileField


def compute_upload_to(value, filename):
    return 'default_path/{}/{}'.format(getattr(value, 'id', 'others/'), filename)


class TestDocument(models.Model):
    documents = FileField(blank=True, upload_to="path/")
    other_documents = FileField(blank=True, upload_to=compute_upload_to)
