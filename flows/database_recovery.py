#!/usr/bin/env python
# coding: utf-8

from prefect_gcp.cloud_storage import GcsBucket
from utils.helper_function import (
    load_from_datalake,
    transformation,
    write_to_warehouse,
)

from prefect import flow


@flow(name="Database Recovery")
def main_flow():
    gcs_bucket_block = "gcp-hongkong-flight-information"
    gcs_bucket = GcsBucket.load(gcs_bucket_block)
    for blob in gcs_bucket.list_blobs("data"):
        file_path = blob.name
        date = file_path[-15:-5]  # YYYY-MM-dd
        data = load_from_datalake(file_path, gcs_bucket_block)
        output_data = transformation(data)
        write_to_warehouse(output_data, date)


if __name__ == '__main__':
    main_flow()
