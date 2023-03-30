import uuid
from os.path import splitext

from PIL import Image

from backoffice.settings.base import OSIS_UPLOAD_FOLDER
from osis_document.exceptions import FormatInvalidException
from osis_document.models import Upload


def convert_file_to_pdf(file_id: uuid) -> str:
    a_file = Upload.objects.get(uuid=file_id)
    if a_file.mimetype in ['application/pdf']:
        return a_file.file.path
    elif a_file.mimetype in ['image/png', 'image/jpg', 'image/jpeg']:
        return _convert_img_to_pdf(file_object=a_file)
    elif a_file.mimetype in ['text/plain', 'application/msword',
                             'application/vnd.oasis.opendocument.text',
                             'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
        return _convert_text_file_to_pdf(file_object=a_file)
    else:
        raise FormatInvalidException


def _convert_img_to_pdf(file_object: Upload) -> str:
    new_file_name = splitext(file_object.metadata['name'])[0] + '.pdf'
    image = Image.open(file_object.file)
    image_pdf = image.convert('RGB')
    image_pdf.save(OSIS_UPLOAD_FOLDER + new_file_name)
    return OSIS_UPLOAD_FOLDER + new_file_name


def _convert_text_file_to_pdf(file_object: Upload) -> str:
    import subprocess
    new_file_name = splitext(file_object.metadata['name'])[0] + '.pdf'
    cmd = subprocess.Popen(
        f'lowriter --headless --convert-to pdf:writer_pdf_Export --outdir /home/stagiaire1/python/projects/osis/osis/uploads/ {file_object.file.path}',
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cmd.communicate()
    return OSIS_UPLOAD_FOLDER + new_file_name
