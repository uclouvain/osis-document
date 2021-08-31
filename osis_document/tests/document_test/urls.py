# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.urls import path, reverse_lazy, include
from django.views.generic import CreateView, UpdateView, DetailView

from osis_document.tests.document_test.models import TestDocument

app_name = 'document_test'
urlpatterns = [
    path(
        '',
        CreateView.as_view(
            model=TestDocument,
            fields='__all__',
            success_url=reverse_lazy('document_test:test-upload'),
        ),
        name='test-upload',
    ),
    path(
        'update/<int:pk>',
        UpdateView.as_view(
            model=TestDocument,
            fields='__all__',
            success_url=reverse_lazy('document_test:test-upload'),
        ),
        name='test-upload',
    ),
    path(
        'view/<int:pk>',
        DetailView.as_view(model=TestDocument,),
        name='test-view',
    ),
    path('document/', include('osis_document.contrib.urls')),
    path('api/', include('osis_document.api.url_v1', namespace="api")),
]
