FROM xanthoustech/cuda-python:11.3.0-cudnn8-py3.9

WORKDIR /opt/server

ADD Pipfile Pipfile.lock /opt/server/

RUN pipenv install --system --deploy

ADD . /opt/server/
