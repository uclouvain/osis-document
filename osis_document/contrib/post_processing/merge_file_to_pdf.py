
from pathlib import Path

from django.core.files import File
from pypdf import PdfMerger

from backoffice.settings.base import OSIS_UPLOAD_FOLDER
from osis_document.enums import PostProcessingType
from osis_document.exceptions import FormatInvalidException
from osis_document.models import Upload, PostProcessing
from osis_document.utils import calculate_hash


def merge_files_to_one_pdf(liste_uuid_files: [], output_file_name: str) -> None:
    input_files = Upload.objects.filter(uuid__in=liste_uuid_files)

    merger = PdfMerger()
    for file in input_files:
        if file.mimetype != "application/pdf":
            raise FormatInvalidException
        merger.append(file.file.path)
    merger.write(f"{OSIS_UPLOAD_FOLDER}{output_file_name}.pdf")
    merger.close()
    pdf_upload_object = create_upload_instance(path=f"{OSIS_UPLOAD_FOLDER}{output_file_name}.pdf")
    create_post_processing_instance(input_files=input_files, output_file=pdf_upload_object)


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


def create_post_processing_instance(input_files: [Upload], output_file: Upload):
    instance = PostProcessing(type=PostProcessingType.MERGE.name)
    instance.save()
    for file in input_files:
        instance.input_files.add(file)
    instance.output_files.add(output_file)

    return instance
