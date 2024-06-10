# from prefect import flow
from prefect_gcp import GcpCredentials
from prefect_gcp.cloud_storage import GcsBucket

# IMPORTANT - do not store credentials in a publicly available repository!

credentials_block = GcpCredentials(
    service_account_info={}  # enter your credentials from the json file
)
credentials_block.save("gcp-creds", overwrite=True)

bucket_block = GcsBucket(
    gcp_credentials=GcpCredentials.load("gcp-creds"),
    bucket="hongkong-flight-information",  # GCS bucket name
)

bucket_block.save("gcp-hongkong-flight-information", overwrite=True)