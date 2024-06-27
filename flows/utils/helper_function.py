#!/usr/bin/env python
# coding: utf-8

import json
import logging
from datetime import datetime, timedelta

import pandas as pd
import psycopg2.extras as p
import requests
from pandas import DataFrame
from prefect_gcp.cloud_storage import GcsBucket

from flows.utils.db_config import get_warehouse_creds
from flows.utils.postgres_db import WarehouseConnection
from prefect import task


@task(log_prints=True)
def get_flights_data(date: str) -> list:
    date_format = date.replace("_", "-")
    is_arrival = 'true'
    is_cargo = 'true'
    json_list = []
    for query_parameters in [
        ('true', 'true'),
        ('true', 'false'),
        ('false', 'true'),
        ('false', 'false'),
    ]:
        is_arrival, is_cargo = query_parameters
        url = (
            f"https://www.hongkongairport.com/flightinfo-rest/rest/flights/"
            f"past?date={date_format}&arrival={is_arrival}&cargo={is_cargo}"
        )
        try:
            r = requests.get(url)
            json_list.extend(r.json())
        except requests.ConnectionError as ce:
            logging.error(f"There was an error with the request, {ce}")
    return json_list


@task(log_prints=True)
def save_to_datalake(data, file_path: str, gcs_bucket_block: str) -> None:
    if "problemNo" in data:
        raise TypeError("json data not extracted properly")

    json_data = json.dumps(data)
    gcs_block = GcsBucket.load(gcs_bucket_block)
    gcs_block.write_path(file_path, json_data)


@task(log_prints=True)
def load_from_datalake(file_path: str, gcs_bucket_block: str):
    gcs_block = GcsBucket.load(gcs_bucket_block)
    data = gcs_block.read_path(file_path)
    data = json.loads(data.decode('utf-8'))
    return data


@task(log_prints=True)
def get_full_load_dates() -> list:
    date_difference = timedelta(days=-89)
    end_date = datetime.today()
    start_date = datetime.today() + date_difference
    return [
        (start_date + timedelta(days=x)).strftime("%Y-%m-%d")
        for x in range((end_date - start_date).days + 1)
    ]


def get_extracted_status_time(row):
    if (
        row['next_datetime'] == 'N/A'
        and (
            row['status'] == 'Cancelled'
            or row['status'] == 'Delayed'
            or row['status'] == 'Boarding'
            or row['status'] == 'Gate Closed'
            or row['status'] == 'Final Call'
            or row['status'] == 'Boarding Soon'
        )
        or row['extract_status_time'] == ''
    ):
        return None
    elif row['next_datetime'] != 'N/A':
        return row['next_datetime']
    else:
        try:
            return row['date'] + ' ' + row['extract_status_time']
        except TypeError:
            logging.error("Exception occurred", exc_info=True)


def is_plane_delayed(row):
    if row['status_timestamp_difference'] < 0 and (
        row['status'] != 'Cancelled' and row['status'] != 'Delayed'
    ):
        return False
    elif row['status_timestamp_difference'] >= 0 and (
        row['status'] != 'Cancelled' and row['status'] != 'Delayed'
    ):
        return True
    else:
        return None


@task(log_prints=True)
def transformation(data) -> DataFrame:
    columns = ['date', 'arrival', 'cargo']
    res = pd.json_normalize(data, 'list', meta=columns)

    # Flights shared between multiple airlines
    res["is_shared_flight"] = res['flight'].apply(
        lambda x: True if len(x) > 1 else False
    )

    # Unpack list of json data with flight information
    res = res.explode('flight')
    df_flight = pd.json_normalize(res.flight)

    # Join main table with flight information
    df = pd.concat(
        [res.drop(['flight'], axis=1).reset_index(), df_flight], axis=1
    )

    # Add empty list as default values
    df['destination'] = df['destination'].apply(
        lambda d: d if isinstance(d, list) else []
    )
    df['origin'] = df['origin'].apply(
        lambda d: d if isinstance(d, list) else []
    )

    # Extract date from status field that represent
    # arrival/departure that occured the next day
    df['next_day'] = df['status'].str.extract(r'(\d+/\d+/\d+)')
    df['next_day'] = df['next_day'].fillna('N/A')

    # Extract time from status field that represent
    # arrival/departure that occured the next day
    df['extract_status_time'] = (
        df['status'].str.extract(r'(\d+:\d+)').fillna('')
    )
    df['next_day'] = df['next_day'].apply(
        (
            lambda x: (
                "{}-{}-{}".format(x[6:], x[3:5], x[:2]) if x != 'N/A' else x
            )
        )
    )

    # Create datetime (string) based on arrival/departure
    # that occured the next day
    df['next_datetime'] = df.apply(
        lambda x: (
            'N/A'
            if x['next_day'] == 'N/A'
            else x['next_day'] + " " + x['extract_status_time']
        ),
        axis=1,
    )

    # Convert datetime to timestamp
    df['datetime'] = df['date'] + ' ' + df['time']
    df['timestamp'] = pd.to_datetime(df['datetime']).astype(int)
    df['timestamp'] = df['timestamp'].div(10**9)

    # Convert datetime to timestamp
    df['extract_status_datetime'] = df.apply(
        lambda x: get_extracted_status_time(x), axis=1
    )
    df['extract_status_timestamp'] = pd.to_datetime(
        df['extract_status_datetime']
    ).astype(int)
    df['extract_status_timestamp'] = df['extract_status_timestamp'].div(10**9)

    # Replace default timestamp values due to NAT datetime values.
    df['extract_status_timestamp'] = df['extract_status_timestamp'].apply(
        lambda x: x if x != -9223372036.854776 else None
    )

    # Create Features
    df['status_timestamp_difference'] = (
        df['extract_status_timestamp'] - df['timestamp']
    )
    df['is_plane_delayed'] = df.apply(lambda x: is_plane_delayed(x), axis=1)
    df['shared_flight_id'] = df['date'] + df['index'].astype(str)
    df['number_origin_countries'] = df['origin'].apply(lambda x: len(x))
    df['number_destination_countries'] = df['destination'].apply(
        lambda x: len(x)
    )
    df['is_multiple_destination'] = df['destination'].apply(
        lambda x: True if len(x) > 1 else False
    )
    df['is_multiple_origin'] = df['origin'].apply(
        lambda x: True if len(x) > 1 else False
    )

    # Drop fields not required anymore
    df = df.drop(
        ['index', 'next_day', 'extract_status_time', 'next_datetime'], axis=1
    )
    df = df.rename(
        columns={
            "no": "flight_number",
            "arrival": "is_arrival",
            "cargo": "is_cargo",
        }
    )

    # Generate json
    data = json.loads(df.to_json(orient='records'))

    return data


def _get_flight_insert_query() -> str:
    return '''
    INSERT INTO airport.flight (
        date,
        time,
        datetime,
        timestamp,
        extract_status_datetime,
        extract_status_timestamp,
        status_timestamp_difference,
        status,
        statusCode,
        origin,
        baggage,
        hall,
        terminal,
        stand,
        destination,
        aisle,
        gate,
        is_arrival,
        is_cargo,
        is_shared_flight,
        flight_number,
        airline,
        is_multiple_destination,
        is_multiple_origin,
        is_plane_delayed,
        shared_flight_id,
        number_origin_countries,
        number_destination_countries
    )
    VALUES (
        %(date)s,
        %(time)s,
        %(datetime)s,
        %(timestamp)s,
        %(extract_status_datetime)s,
        %(extract_status_timestamp)s,
        %(status_timestamp_difference)s,
        %(status)s,
        %(statusCode)s,
        %(origin)s,
        %(baggage)s,
        %(hall)s,
        %(terminal)s,
        %(stand)s,
        %(destination)s,
        %(aisle)s,
        %(gate)s,
        %(is_arrival)s,
        %(is_cargo)s,
        %(is_shared_flight)s,
        %(flight_number)s,
        %(airline)s,
        %(is_multiple_destination)s,
        %(is_multiple_origin)s,
        %(is_plane_delayed)s,
        %(shared_flight_id)s,
        %(number_origin_countries)s,
        %(number_destination_countries)s
    );
    '''


@task(log_prints=True)
def write_to_warehouse(data, date) -> None:
    date_format = date.replace("_", "-")
    with WarehouseConnection(get_warehouse_creds()).managed_cursor() as curr:
        curr.execute(
            (
                f"SELECT COUNT(*) FROM "
                f"airport.flight WHERE date ='{date_format}';"
            )
        )
        count_rows = curr.fetchall()
        print("num of rows", count_rows)
        if count_rows == 0:
            p.execute_batch(curr, _get_flight_insert_query(), data)
            logging.info("Data inserted into the database")
        else:
            logging.info("Data already exists in the database")
