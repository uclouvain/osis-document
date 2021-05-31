from django.db import models

from osis_document.contrib.fields import FileField


class TestDocument(models.Model):
    documents = FileField()
