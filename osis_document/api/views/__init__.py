# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from .editor import SaveEditorView
from .metadata import MetadataView, ChangeMetadataView, MetadataListView
from .post_processing import PostProcessingView, GetProgressAsyncPostProcessingView
from .raw_file import RawFileView
from .rotate import RotateImageView
from .security import DeclareFileAsInfectedView
from .token import GetTokenView, GetTokenListView
from .upload import ConfirmUploadView, RequestUploadView

__all__ = [
    "RawFileView",
    "MetadataView",
    "MetadataListView",
    "ChangeMetadataView",
    "ConfirmUploadView",
    "RequestUploadView",
    "GetTokenView",
    "GetTokenListView",
    "RotateImageView",
    "DeclareFileAsInfectedView",
    'PostProcessingView',
    "SaveEditorView",
    "GetProgressAsyncPostProcessingView",
]
