FROM prefecthq/prefect:2.12.1-python3.11

COPY ./containers/prefect-server/requirements.txt .
COPY --chmod=777 startup.sh /opt/prefect/
COPY /blocks/ /opt/prefect/blocks

RUN apt update
RUN pip install -r requirements.txt --trusted-host pypi.python.org --no-cache-dir
