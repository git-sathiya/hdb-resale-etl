from pathlib import Path
import pandas as pd

def load_all_csv(input_dir: Path) -> pd.DataFrame:
    files = sorted(input_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found in {input_dir}")

    dfs = []
    for f in files:
        df = pd.read_csv(f)
        df["source_file"] = f.name
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True, sort=False)
    return combined
