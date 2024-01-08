# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from setuptools import setup, find_packages

setup(
    name='OSIS Document',
    version='0.9.12',
    description='Document management API and widget',
    url='http://github.com/uclouvain/osis-document',
    author='Université catholique de Louvain',
    author_email='O365G-team-osis-dev@groupes.uclouvain.be',
    license='AGPLv3',
    packages=find_packages(exclude=('osis_document.tests',)),
    include_package_data=True,
    install_requires=[
        'requests>=2.20.0,<3.0',
        'filetype>=1.1.0,<2.0',
        'pypdf>=3.6.0,<4.0',
        'python-magic==0.4.27'
    ]
)
