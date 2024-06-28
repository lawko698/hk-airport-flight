"""
create flight table
"""

from yoyo import step

__depends__ = {"20240603_01_create_airport_schema"}

steps = [
    step(
        """
        CREATE TABLE airport.flight
        (
            id BIGINT,
            date VARCHAR(50),
            time VARCHAR(50),
            datetime TIMESTAMP,
            timestamp BIGINT,
            extract_status_datetime TIMESTAMP,
            extract_status_timestamp BIGINT,
            status_timestamp_difference BIGINT,
            status VARCHAR(100),
            statusCode VARCHAR(100),
            origin VARCHAR(100),
            baggage VARCHAR(50),
            hall VARCHAR(50),
            terminal VARCHAR(50),
            stand VARCHAR(50),
            destination VARCHAR(50),
            aisle VARCHAR(10),
            gate VARCHAR(10),
            is_arrival BOOLEAN,
            is_cargo BOOLEAN,
            is_shared_flight VARCHAR(100),
            flight_number VARCHAR(100),
            airline VARCHAR(100),
            is_multiple_destination BOOLEAN,
            is_multiple_origin BOOLEAN,
            is_plane_delayed BOOLEAN,
            number_origin_countries VARCHAR(100),
            number_destination_countries VARCHAR(100),
            PRIMARY KEY (id)
        )
        """,
        "DROP TABLE airport.flight",
    )
]