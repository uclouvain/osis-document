from abc import ABC, abstractmethod

from osis_document.models import Upload, PostProcessing


class Converteur(ABC):

    @abstractmethod
    def convert(self, upload_object: Upload) -> PostProcessing:
        pass

    @staticmethod
    @abstractmethod
    def get_supported_format() -> list:
        pass

    @staticmethod
    @abstractmethod
    def create_upload_instance(path: str) -> Upload:
        pass

    @staticmethod
    @abstractmethod
    def create_post_processing_instance(input_object: Upload, output_object: Upload) -> PostProcessing:
        pass
