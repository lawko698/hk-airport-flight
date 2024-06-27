#!/usr/bin/env python
# coding: utf-8

import argparse
from datetime import datetime

from utils.helper_function import (
    get_flights_data,
    load_from_datalake,
    save_to_datalake,
    transformation,
    write_to_warehouse,
)

from prefect import flow


@flow(name="Incremental Load Ingestion")
def main_flow():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--date',
        nargs='?',
        help='Date used for ETL flight data. Format(YYYY_MM_dd)',
    )
    args = parser.parse_args()

    if not args.date:
        date = datetime.today().strftime('%Y_%m_%d')
    else:
        date = args.date

    gcs_bucket_block = "gcp-hongkong-flight-information"
    file_path = f"raw_hong_kong_flight_information_{date}.json"

    data = get_flights_data(date)
    save_to_datalake(data, file_path, gcs_bucket_block)

    data = load_from_datalake(file_path, gcs_bucket_block)
    output_data = transformation(data)
    write_to_warehouse(output_data, date)


if __name__ == '__main__':
    main_flow.serve(name="Incremental Load", cron="0 6 * * *")  # type: ignore
