from pathlib import Path
from typing import Union
import os
import requests
import time
import tempfile

from .config import STORAGE_TYPE, S3_BUCKET, S3_PREFIX

# ---------------------------------------------------------------------------
# Local helpers
# ---------------------------------------------------------------------------

def _download_to_local(url: str, output_path: Path) -> dict:
    """Download *url* to *output_path* on the local filesystem."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        return {"file": output_path.name, "status": "exists"}

    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    return {"file": output_path.name, "status": "downloaded"}

# ---------------------------------------------------------------------------
# S3 helpers
# ---------------------------------------------------------------------------

def _s3_key_exists(s3_client, bucket: str, key: str) -> bool:
    """Return True if *key* already exists in *bucket*."""
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except s3_client.exceptions.ClientError:
        return False
    except Exception:
        # If boto3 is not available or any other error, assume not exists
        return False

def _upload_to_s3(local_path: Path, bucket: str, key: str):
    """Upload *local_path* to S3 *bucket* at *key*."""
    import boto3
    s3 = boto3.client("s3")
    print(f"  Uploading {local_path.name} → s3://{bucket}/{key} …")
    s3.upload_file(str(local_path), bucket, key)
    print(f"  Upload complete: s3://{bucket}/{key}")

def _download_to_s3(url: str, filename: str) -> dict:
    """Download *url* to a temp file, then upload it to S3. Returns status dict."""
    import boto3

    s3 = boto3.client("s3")
    key = f"{S3_PREFIX}/input/{filename}".lstrip("/")

    # Check if already on S3
    try:
        s3.head_object(Bucket=S3_BUCKET, Key=key)
        print(f"  Dataset already exists in S3: s3://{S3_BUCKET}/{key}. Skipping.")
        return {"file": filename, "status": "exists"}
    except s3.exceptions.ClientError:
        pass  # not found, proceed with download + upload
    except Exception:
        pass

    # Download to a temp file then upload
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp_path = Path(tmp.name)

    try:
        print(f"  Downloading to temp file: {tmp_path} …")
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        with open(tmp_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        _upload_to_s3(tmp_path, S3_BUCKET, key)
        return {"file": filename, "status": "uploaded_to_s3"}
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

# ---------------------------------------------------------------------------
# Public entry-point
# ---------------------------------------------------------------------------

def main():
    # Determine the local input directory (used in local mode only)
    input_dir = Path(__file__).resolve().parent.parent / "data" / "input"

    # Dataset IDs from collection 189
    dataset_ids = [
        "d_ebc5ab87086db484f88045b47411ebc5",  # 1990 - 1999
        "d_ea9ed51da2787afaf8e51f827c304208",  # 2000 - Feb 2012
        "d_43f493c6c50d54243cc1eab0df142d6a",  # Mar 2012 - Dec 2014
        "d_2d5ff9ea31397b66239f245f57751537",  # Jan 2015 - Dec 2016
        "d_8b84c4ee58e3cfc0ece0d773c8ca6abc",  # Jan 2017 - Present
    ]

    results = []
    for d_id in dataset_ids:
        filename = f"{d_id}.csv"

        # ---------- local mode: skip if already on disk ----------
        if STORAGE_TYPE == "local":
            input_dir.mkdir(parents=True, exist_ok=True)
            dest_path = input_dir / filename
            if dest_path.exists():
                print(f"Dataset {d_id} already exists locally. Skipping.")
                results.append({"file": filename, "status": "exists"})
                time.sleep(1)
                continue

        print(f"Initiating download for dataset: {d_id}")
        initiate_url = (
            f"https://api-open.data.gov.sg/v1/public/api/datasets/{d_id}/initiate-download"
        )

        try:
            response = requests.get(initiate_url, timeout=30)
            response.raise_for_status()
            res_json = response.json()

            if res_json.get("code") == 0:
                download_url = res_json["data"]["url"]

                if STORAGE_TYPE == "s3":
                    result = _download_to_s3(download_url, filename)
                else:
                    dest_path = input_dir / filename
                    print(f"  Downloading to {dest_path} …")
                    result = _download_to_local(download_url, dest_path)

                results.append(result)
                print(f"  Finished: {result}")

            else:
                error_msg = res_json.get("errorMsg", "Unknown error")
                print(f"Failed to initiate download for {d_id}: {error_msg}")
                results.append({"dataset_id": d_id, "status": "failed", "error": error_msg})

        except Exception as e:
            print(f"Error handling dataset {d_id}: {e}")
            results.append({"dataset_id": d_id, "status": "error", "error": str(e)})

        # Sleep to avoid rate limiting (429)
        time.sleep(3)

    return results


if __name__ == "__main__":
    print(main())
