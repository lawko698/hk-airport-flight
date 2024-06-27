FROM prefecthq/prefect:2.12.1-python3.11

COPY ./containers/requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt --trusted-host pypi.python.org --no-cache-dir
