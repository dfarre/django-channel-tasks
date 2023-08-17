FROM ubuntu:latest

ENV PYTHONUNBUFFERED 1

RUN apt-get -y update
RUN apt-get -y install git python3-pip python3-dev postgresql-client locales
RUN sed -i '/C.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

RUN mkdir /code
WORKDIR /code
ADD setup.py MANIFEST.in README.md version.ini /code/
RUN pip3 install --upgrade pip
RUN pip3 install -e .[dev,test]
RUN pip3 install tox
ADD . /code/
