# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
import uuid
from pathlib import Path
from typing import List
from uuid import UUID

from django.core.files import File
from django.db.models import Q
from osis_document.enums import PostProcessingType
from osis_document.exceptions import FormatInvalidException, MissingFileException
from osis_document.models import Upload, PostProcessing
from osis_document.utils import calculate_hash
from pypdf import PaperSize, PageObject, PdfReader, PdfWriter

from backoffice.settings.base import OSIS_UPLOAD_FOLDER


class Merger:
    def process(self, input_uuid_files: list, **kwargs) -> List[UUID]:
        filename = kwargs.pop('filename', None)
        pages_dimension = kwargs.pop('pages_dimension', None)
        input_files = Upload.objects.filter(
            Q(uuid__in=input_uuid_files) | Q(output_files__uuid__in=input_uuid_files)
        ).distinct('uuid')
        if len(input_files) != len(input_uuid_files):
            raise MissingFileException
        writer_pdf = PdfWriter()
        for file in input_files:
            if file.mimetype != "application/pdf":
                raise FormatInvalidException
            reader = PdfReader(stream=file.file.path)
            if pages_dimension:
                writer_pdf = self._merge_and_change_pages_dimension(
                    writer_instance=writer_pdf,
                    pages=reader.pages,
                    dimension=pages_dimension
                )
            else:
                writer_pdf.append_pages_from_reader(reader=reader)
        path = f'{OSIS_UPLOAD_FOLDER}{self._get_output_filename(filename)}'
        writer_pdf.write(path)
        writer_pdf.close()
        pdf_upload_object = self._create_upload_instance(path=path)
        self._create_post_processing_instance(
            input_files=input_files, output_file=pdf_upload_object
        )
        return [pdf_upload_object.uuid]

    @staticmethod
    def _merge_and_change_pages_dimension(writer_instance: PdfWriter, pages: List[PageObject], dimension):
        expected_page_width = getattr(PaperSize, dimension).width
        for page in pages:
            current_page_width = page.mediabox.width
            if current_page_width > expected_page_width:
                y_translation_factor = expected_page_width / current_page_width
                page.scale_to(
                    expected_page_width,
                    page.mediabox.height * y_translation_factor,
                )
            writer_instance.add_page(page=page)
        return writer_instance

    @staticmethod
    def _get_output_filename(filename: str):
        if filename:
            return f"{filename}.pdf"
        else:
            return f"merge_{uuid.uuid4()}.pdf"

    @staticmethod
    def _create_upload_instance(path: str) -> Upload:
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
    def _create_post_processing_instance(input_files: [Upload], output_file: Upload):
        instance = PostProcessing(type=PostProcessingType.MERGE.name)
        instance.save()
        for file in input_files:
            instance.input_files.add(file)
        instance.output_files.add(output_file)
        return instance


merger = Merger()
