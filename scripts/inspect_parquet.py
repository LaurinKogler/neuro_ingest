from neuro_ingest.io import load_session_parquet
from pathlib import Path

p = Path(r"E:\data_noise\normalized\AC04_20251017__TDT.parquet")
df = load_session_parquet(p)

print(df.head())
print(df[["freq_hz", "level_db"]].drop_duplicates().sort_values(["freq_hz", "level_db"]).head(30))
print("Columns:", df.columns.tolist())
print(df["level_db"].describe())
print(df[["freq_hz", "level_db"]].drop_duplicates().sort_values(["freq_hz", "level_db"]))
