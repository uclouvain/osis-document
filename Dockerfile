FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libjpeg-dev \
        libz-dev \
        libfreetype6-dev \
        liblcms2-dev \
        libopenjp2-7-dev \
        libtiff5-dev \
        build-essential \
        libmagic1 \
        libwebp-dev && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /osis-document

RUN pip install --upgrade pip && \
    pip install python-magic

COPY ./docker/server/requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

COPY ./docker/server/django-server-entrypoint.sh ./django-server-entrypoint.sh
COPY ./docker/server/manage.py ./manage.py
COPY ./docker/server/document ./document
COPY ./osis_document /osis-document/osis_document
COPY ./debug /osis-document/debug

RUN chmod +x ./django-server-entrypoint.sh && \
    rm -rf ~/.cache/pip

EXPOSE 9503
ENTRYPOINT ["./django-server-entrypoint.sh"]
