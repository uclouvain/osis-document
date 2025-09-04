##############################################################################
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
##############################################################################
from django.conf import settings
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Tracer


def initialize():
    resource = Resource(attributes={
        "service.name": getattr(settings, 'OTEL_SERVICE_NAME', 'OSIS-DOCUMENT')
    })
    provider = TracerProvider(resource=resource)
    otlp_exporter = OTLPSpanExporter(
        endpoint=getattr(settings, 'OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4317'),
        insecure=bool(getattr(settings, 'OTEL_EXPORTER_OTLP_INSECURE', False)),
    )
    processor = BatchSpanProcessor(otlp_exporter)  # ConsoleSpanExporter()
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)


def initialize_instrumentation():
    DjangoInstrumentor().instrument(tracer_provider=trace.get_tracer_provider(), is_sql_commentor_enabled=True)
    Psycopg2Instrumentor().instrument(
        tracer_provider=trace.get_tracer_provider(),
        skip_dep_check=True,  # We use psycopg2-binary so we must skip dep check
        enable_commenter=True,
        commenter_options={},
    )
    URLLib3Instrumentor().instrument(tracer_provider=trace.get_tracer_provider(), skip_dep_check=True)
    RequestsInstrumentor().instrument(tracer_provider=trace.get_tracer_provider())
    CeleryInstrumentor().instrument(trace_provider=trace.get_tracer_provider())


def get_tracer() -> Tracer:
    return trace.get_tracer(settings.OTEL_TRACER_MODULE_NAME, settings.OTEL_TRACER_LIBRARY_VERSION)
