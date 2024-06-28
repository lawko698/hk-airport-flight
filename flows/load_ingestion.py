#!/usr/bin/env python
# coding: utf-8

import argparse

from utils.helper_function import (
    get_flights_data,
    load_from_datalake,
    save_to_datalake,
    transformation,
    validate_datetime_format,
    write_to_warehouse,
)

from prefect import flow


@flow(name="Load Ingestion")
def main_flow():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--date',
        required=True,
        help='Date used for ETL flight data. Format(YYYY-MM-dd)',
    )
    args = parser.parse_args()
    date = args.date
    validate_datetime_format(date)

    gcs_bucket_block = "gcp-hongkong-flight-information"
    file_path = f"data/raw_hong_kong_flight_information_{date}.json"

    data = get_flights_data(date)
    save_to_datalake(data, file_path, gcs_bucket_block)

    data = load_from_datalake(file_path, gcs_bucket_block)
    output_data = transformation(data)
    write_to_warehouse(output_data, date)


if __name__ == '__main__':
    main_flow()
