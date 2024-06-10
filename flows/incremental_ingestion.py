#!/usr/bin/env python
# coding: utf-8

from prefect import flow
from datetime import datetime
from utils.helper_function import get_flights_data, save_to_datalake, load_from_datalake, transformation, write_to_warehouse

@flow(name="Incremental Load Ingestion")
def main_flow():
    gcs_bucket_block = "gcp-hongkong-flight-information"
    date = datetime.today().strftime('%Y_%m_%d')
    file_path = f"raw_hong_kong_flight_information_{date}.json"

    data = get_flights_data(date)
    save_to_datalake(data, file_path, gcs_bucket_block)

    data = load_from_datalake(file_path, gcs_bucket_block)
    output_data = transformation(data)
    write_to_warehouse(output_data)

if __name__ == '__main__':
    main_flow.serve(name="Incremental Load", cron="0 6 * * *")
