FROM python:3.9.5

COPY ./migrations/ /opt/migrations

RUN apt-get update

COPY ./containers/requirements.txt .

RUN pip install -r requirements.txt --trusted-host pypi.python.org --no-cache-dir
