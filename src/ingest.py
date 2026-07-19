from pathlib import Path
import requests
import time

def download_file(url: str, output_path: Path):
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

def main():
    input_dir = Path("data/input")
    input_dir.mkdir(parents=True, exist_ok=True)

    # Dataset IDs from collection 189
    dataset_ids = [
        "d_ebc5ab87086db484f88045b47411ebc5",  # 1990 - 1999
        "d_ea9ed51da2787afaf8e51f827c304208",  # 2000 - Feb 2012
        "d_43f493c6c50d54243cc1eab0df142d6a",  # Mar 2012 - Dec 2014
        "d_2d5ff9ea31397b66239f245f57751537",  # Jan 2015 - Dec 2016
        "d_8b84c4ee58e3cfc0ece0d773c8ca6abc"   # Jan 2017 - Present
    ]

    results = []
    for d_id in dataset_ids:
        filename = f"{d_id}.csv"
        dest_path = input_dir / filename
        
        if dest_path.exists():
            print(f"Dataset {d_id} already exists locally. Skipping API call.")
            results.append({"file": filename, "status": "exists"})
            continue

        print(f"Initiating download for dataset: {d_id}")
        initiate_url = f"https://api-open.data.gov.sg/v1/public/api/datasets/{d_id}/initiate-download"
        try:
            response = requests.get(initiate_url, timeout=30)
            response.raise_for_status()
            res_json = response.json()
            if res_json.get("code") == 0:
                download_url = res_json["data"]["url"]
                print(f"Downloading to {dest_path}...")
                result = download_file(download_url, dest_path)
                results.append(result)
                print(f"Finished: {result}")
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


