from pathlib import Path
import pandas as pd
from prefect import flow, task
from prefect_gcp.cloud_storage import GcsBucket
from random import randint
from prefect.tasks import task_input_hash
from datetime import timedelta

@task(retries=3, cache_key_fn=task_input_hash, cache_expiration=timedelta(days=1))
def fetch(dataset_url: str) ->pd.DataFrame:  # Read data from web into pandas dataFrame
    #if randint(0,1) > 0:
        #raise Exception
    
    df = pd.read_csv(dataset_url)
    return df

@task(log_prints=True)
def clean_up (df=pd.DataFrame)->pd.DataFrame:   #Fixing dtype issues
    df['tpep_pickup_datetime'] = pd.to_datetime(df["tpep_pickup_datetime"])
    df['tpep_pickup_datetime'] = pd.to_datetime(df["tpep_pickup_datetime"])
    print(df.head(2))
    print(f"columns: {df.dtypes}")
    print(f"rows: {len(df)}")
    return df


@task ()

def write_local(df:pd.DataFrame, color:str, dataset_file:str) -> Path:  # Writing DataFrame out locally as a parquet file
    path = Path(f"data/{color}/{dataset_file}.parquet") 
    df.to_parquet(path, compression="gzip")
    return path 

@task()
def write_gcs(path: Path) -> None:  #uploading local parquet to google cloud
    gcp_cloud_storage_bucket_block = GcsBucket.load("zoomcamp-gcs")
    gcp_cloud_storage_bucket_block.upload_from_path(from_path = f"{path}",to_path=path)
    return

@flow()
def etl_web_to_gcs(year: int, month: int, color: str )-> None: #this is the main etl function

    dataset_file = f"{color}_tripdata_{year}-{month:02}"
    dataset_url = f"https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{color}/{dataset_file}.csv.gz"

    df = fetch(dataset_url)
    df_clean = clean_up (df)
    path = write_local(df_clean, color, dataset_file)
    write_gcs(path)

@flow()
def etl_parent_flow(
    months: list[int] = [1, 2], year: int = 2021, color: str = "yellow"
):
    for month in months:
        etl_web_to_gcs(year, month, color)


if __name__=='__main__':

    color = "green"
    months = [9,10,11,12]
    year = 2019
    etl_parent_flow(months, year, color)