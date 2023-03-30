from os.path import splitext
from pathlib import Path
from xdrlib import ConversionError

from PIL import Image
from django.core.files import File
from osis_document.contrib.post_processing.converteur.converteur import Converter
from osis_document.enums import PostProcessingType
from osis_document.exceptions import FormatInvalidException
from osis_document.models import Upload, PostProcessing
from osis_document.utils import calculate_hash

from backoffice.settings.base import OSIS_UPLOAD_FOLDER


class ConverterImageToPdf(Converter):

    def convert(self, upload_object: Upload) -> PostProcessing:
        if upload_object.mimetype not in self.get_supported_format():
            raise FormatInvalidException
        try:
            new_file_name = splitext(upload_object.metadata['name'])[0] + '.pdf'
            image = Image.open(upload_object.file)
            image_pdf = image.convert('RGB')
            image_pdf.save(OSIS_UPLOAD_FOLDER + new_file_name)
            pdf_upload_object = self.create_upload_instance(path=OSIS_UPLOAD_FOLDER + new_file_name)
            post_processing_object = self.create_post_processing_instance(input_object=upload_object, output_object=pdf_upload_object)
            return post_processing_object
        except Exception:
            raise ConversionError

    @staticmethod
    def get_supported_format() -> list:
        return ['image/png', 'image/jpg', 'image/jpeg']

    @staticmethod
    def create_upload_instance(path: str) -> Upload:
        with Path(path).open(mode='rb') as f:
            file = File(f, name=Path(path).name)
            instance = Upload(
                mimetype="application/pdf",
                size=file.size,
                metadata={'hash': calculate_hash(file), 'name': file.name},
            )
            instance.file = Path(path).name
            instance.file.file = file
            instance.save()
            return instance

    @staticmethod
    def create_post_processing_instance(input_object: Upload, output_object: Upload) -> PostProcessing:
        instance = PostProcessing(type=PostProcessingType.CONVERT.name)
        instance.save()
        instance.input_files.add(input_object)
        instance.output_files.add(output_object)
        return instance
