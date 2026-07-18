from pathlib import Path
import requests

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

    # Replace these URLs with the actual dataset file URLs from data.gov.sg metadata
    file_urls = [
        # "https://...csv",
        https://data.gov.sg/collections/189/view
    ]

    results = []
    for url in file_urls:
        filename = url.split("/")[-1].split("?")[0]
        result = download_file(url, input_dir / filename)
        results.append(result)

    return results

if __name__ == "__main__":
    print(main())
