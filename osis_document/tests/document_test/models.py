from django.db import models

from osis_document.contrib.fields import FileField
from osis_document.enums import DocumentExpirationPolicy


def compute_upload_to(value, filename):
    return 'default_path/{}/{}'.format(getattr(value, 'id', 'others/'), filename)


class TestDocument(models.Model):
    documents = FileField(blank=True, upload_to="path/")
    other_documents = FileField(blank=True, upload_to=compute_upload_to)
    documents_expirables = FileField(
        blank=True,
        upload_to="path/",
        document_expiration_policy=DocumentExpirationPolicy.EXPORT_EXPIRATION_POLICY.value,
    )
