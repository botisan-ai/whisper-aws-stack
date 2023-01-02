FROM xanthoustech/cuda-python:11.3.0-cudnn8-py3.9

RUN apt-get install -y libcurl4-openssl-dev libssl-dev python3.9-dev

WORKDIR /opt/server

ADD Pipfile Pipfile.lock /opt/server/

ENV PIPENV_VERSION=false

RUN pipenv install --system --deploy

ADD . /opt/server/
