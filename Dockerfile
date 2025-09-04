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
        libwebp-dev \
        default-jre \
        libreoffice \
        gettext && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app

RUN pip install --upgrade pip && \
    pip install python-magic

COPY ./requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

ADD . /app

RUN chmod +x /app/docker/server/django-server-entrypoint.sh && \
    rm -rf ~/.cache/pip

EXPOSE 9503
ENTRYPOINT ["/app/docker/server/django-server-entrypoint.sh"]
