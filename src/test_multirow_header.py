#!/usr/bin/env python3
"""2行ヘッダー解析テストスクリプト"""

from csv_fetcher import CSVFetcher
from constants import SPREADSHEET_ID, SONGS_GID
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("TESTING MULTIROW HEADER PARSING")
print("=" * 80)

fetcher = CSVFetcher()

# Fetch with multirow header parsing
df = fetcher.fetch_csv_as_dataframe(
    SPREADSHEET_ID,
    SONGS_GID,
    header=1,
    use_multirow_header=True
)

print(f"\n📊 DataFrame Info:")
print(f"  Total columns: {len(df.columns)}")
print(f"  Total rows: {len(df)}")

print(f"\n🔍 First 20 column names:")
print("-" * 80)
for i, col in enumerate(df.columns[:20], 1):
    print(f"{i:3d}. {col}")

print(f"\n🔍 Checking for .1 suffix columns:")
print("-" * 80)
suffixed_cols = [col for col in df.columns if '.1' in col]
if suffixed_cols:
    print(f"⚠️  Found {len(suffixed_cols)} columns with .1 suffix:")
    for col in suffixed_cols:
        print(f"  - {col}")
else:
    print("✅ No .1 suffix columns found!")

print(f"\n🔍 Notes columns (Shout/Beat/Melody):")
print("-" * 80)
notes_cols = [col for col in df.columns if
              ('Shout' in col or 'Beat' in col or 'Melody' in col)
              and (col.endswith('白') or col.endswith('色'))]
print(f"Found {len(notes_cols)} notes columns:")
for col in notes_cols[:10]:
    print(f"  - {col}")
if len(notes_cols) > 10:
    print(f"  ... and {len(notes_cols) - 10} more")

print("\n" + "=" * 80)
