# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from drf_spectacular.generators import SchemaGenerator

OSIS_DOCUMENT_SDK_VERSION = "1.0.6"


class OsisDocumentSchemaGenerator(SchemaGenerator):
    def get_schema(self, *args, **kwargs):
        schema = super().get_schema(*args, **kwargs)
        schema["openapi"] = "3.0.0"
        schema["info"]["title"] = "OSIS Document Service"
        schema["info"]["version"] = OSIS_DOCUMENT_SDK_VERSION
        schema["info"]["description"] = "A set of API endpoints that allow you to get information about uploads"
        schema["info"]["contact"] = {
            "name": "UCLouvain - OSIS",
            "url": "https://github.com/uclouvain/osis",
        }
        schema["servers"] = [
            {
                "url": "https://{environment}.osis.uclouvain.be/api/v1/osis_document/",
                "variables": {
                    "environment": {
                        "default": "dev",
                        "enum": [
                            "dev",
                            "qa",
                            "test",
                        ]
                    }
                },
            },
            {
                "url": "https://osis.uclouvain.be/api/v1/osis_document/",
                "description": "Production server",
            },
        ]
        schema['components']["securitySchemes"] = {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-KEY",
            }
        }
        schema['components'].setdefault('responses', {}).update({
            "Unauthorized": {
                "description": "Unauthorized",
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}},
            },
            "BadRequest": {
                "description": "Bad request",
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}},
            },
            "NotFound": {
                "description": "The specified resource was not found",
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}},
            },
        })
        schema['components']['schemas']['Error'] = {
            "type": "object",
            "properties": {
                "error": {
                    "type": "string",
                },
            },
        }
        schema['components']['schemas']['ErrorWithStatus'] = {
            "type": "object",
            "properties": {
                "error": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                        },
                        "message": {
                            "type": "string",
                        },
                    },
                },
            },
        }
        schema["components"]["schemas"]["Upload"] = {
            "type": "object",
            "properties": {
                "upload_id": {
                    "type": "string",
                    "format": "uuid",
                },
            }
        }
        for path, path_content in schema['paths'].items():
            for method, method_content in path_content.items():
                method_content['responses'].update(
                    {
                        "400": {"$ref": "#/components/responses/BadRequest"},
                        "401": {"$ref": "#/components/responses/Unauthorized"},
                        "404": {"$ref": "#/components/responses/NotFound"},
                    }
                )
        return schema
