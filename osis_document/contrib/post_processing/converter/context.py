from osis_document.contrib.post_processing.converter.converter import Converter
from osis_document.models import Upload


class Context:

    def __init__(self, converter: Converter, upload_object: Upload) -> None:
        self._upload_object = upload_object
        self._converter = converter

    @property
    def converter(self) -> Converter:
        return self._converter

    @property
    def upload_object(self) -> Upload:
        return self._upload_object

    @converter.setter
    def converter(self, converter: Converter) -> None:
        self._converter = converter

    @upload_object.setter
    def upload_object(self, upload_object: Upload) -> None:
        self._upload_object = upload_object

    def make_conversion(self) -> None:
        self._converter.convert(upload_object=self._upload_object)
