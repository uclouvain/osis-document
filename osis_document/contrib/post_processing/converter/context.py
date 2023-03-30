from osis_document.contrib.post_processing.converteur.converteur import Converteur
from osis_document.models import Upload


class Context:

    def __init__(self, converteur: Converteur, upload_object: Upload) -> None:
        self._upload_object = upload_object
        self._converteur = converteur

    @property
    def converteur(self) -> Converteur:
        return self._converteur

    @property
    def upload_object(self) -> Upload:
        return self._upload_object

    @converteur.setter
    def converteur(self, converteur: Converteur) -> None:
        self._converteur = converteur

    @upload_object.setter
    def upload_object(self, upload_object: Upload) -> None:
        self._upload_object = upload_object

    def make_conversion(self) -> None:
        self._converteur.convert(upload_object=self._upload_object)
