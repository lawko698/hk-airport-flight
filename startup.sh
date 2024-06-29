#!/usr/bin/env bash

prefect block register --file blocks/make_gcp_blocks.py
python blocks/make_gcp_blocks.py
python flows/full_load_ingestion.py
python flows/schedule_incremental_ingestion.py
