"""
Download Passenger Volume by Origin-Destination data from LTA DataMall.

Downloads Bus OD and Train OD data for all available months.
API workflow:
  1. Call API endpoint → get temporary S3 pre-signed URL (Link field)
  2. Download zip file from that URL (expires in ~5 minutes)
  3. Extract CSV from zip → save to data/OD_Data/

Usage:
    python utils/download_od_data.py
    python utils/download_od_data.py --start 202401 --end 202602
    python utils/download_od_data.py --test    # only download one month to test
"""

import json
import time
import urllib.request
import zipfile
import io
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from calendar import monthrange

# === Config ===
API_KEY = "tn4cbt0yTiOl6gtoB9rwqg=="
HEADERS = {"AccountKey": API_KEY, "accept": "application/json"}

BUS_OD_URL = "https://datamall2.mytransport.sg/ltaodataservice/PV/ODBus?Date={ym}"
TRAIN_OD_URL = "https://datamall2.mytransport.sg/ltaodataservice/PV/ODTrain?Date={ym}"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "OD_Data"

MAX_RETRIES = 3
RETRY_DELAY = 10
REQUEST_DELAY = 3  # seconds between API calls to avoid rate limiting

# Expected CSV filenames inside the zip (LTA convention)
BUS_OD_CSV = "origin_destination_bus_{}.csv"
TRAIN_OD_CSV = "origin_destination_train_{}.csv"


def get_download_link(url: str, label: str) -> str:
    """Call LTA API and return the temporary S3 download link."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            value = data.get("value")
            if not value:
                raise ValueError(f"No 'value' field in API response: {list(data.keys())}")

            # value is a list of dicts, each with a "Link" key
            if isinstance(value, list):
                link = value[0].get("Link")
            elif isinstance(value, dict):
                link = value.get("Link")
            else:
                link = str(value)

            if not link:
                raise ValueError(f"No 'Link' found in value: {json.dumps(value)[:200]}")

            return link

        except Exception as e:
            print(f"    [{label}] Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                print(f"    Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                raise


def download_and_extract(link: str, csv_filename: str, label: str) -> bool:
    """Download zip from S3 link and extract CSV to DATA_DIR."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / csv_filename

    # Skip if already downloaded
    if out_path.exists() and out_path.stat().st_size > 0:
        print(f"    [{label}] Already exists: {csv_filename} ({out_path.stat().st_size / 1024 / 1024:.1f} MB)")
        return True

    try:
        req = urllib.request.Request(link)
        with urllib.request.urlopen(req, timeout=300) as resp:
            zip_data = resp.read()

        # Extract CSV from zip
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            # List contents
            names = zf.namelist()
            # Find the CSV file (usually the only file, or the .csv one)
            csv_name = None
            for n in names:
                if n.lower().endswith(".csv"):
                    csv_name = n
                    break
            if csv_name is None:
                # If no .csv found, take the first file
                csv_name = names[0]
                print(f"    [{label}] Warning: no .csv in zip, using: {csv_name}")

            csv_content = zf.read(csv_name)

        with open(out_path, "wb") as f:
            f.write(csv_content)

        size_mb = out_path.stat().st_size / 1024 / 1024
        print(f"    [{label}] Saved: {csv_filename} ({size_mb:.1f} MB)")
        return True

    except Exception as e:
        print(f"    [{label}] Download failed: {e}")
        # Clean up partial file
        if out_path.exists():
            out_path.unlink()
        return False


def download_month(year_month: str) -> dict:
    """Download Bus OD and Train OD for a single month."""
    results = {}

    for pt_type, url_template, csv_template in [
        ("Bus", BUS_OD_URL, BUS_OD_CSV),
        ("Train", TRAIN_OD_URL, TRAIN_OD_CSV),
    ]:
        label = f"{pt_type} {year_month}"
        api_url = url_template.format(ym=year_month)
        csv_filename = csv_template.format(year_month)

        try:
            # Step 1: Get download link
            link = get_download_link(api_url, label)
            time.sleep(1)  # Brief pause before downloading

            # Step 2: Download and extract
            success = download_and_extract(link, csv_filename, label)
            results[label] = success

        except Exception as e:
            print(f"    [{label}] FAILED: {e}")
            results[label] = False

        # Rate limiting between requests
        time.sleep(REQUEST_DELAY)

    return results


def generate_months(start_ym: str, end_ym: str) -> list:
    """Generate list of YYYYMM strings from start to end (inclusive)."""
    months = []
    current = datetime.strptime(start_ym, "%Y%m")
    end = datetime.strptime(end_ym, "%Y%m")

    while current <= end:
        months.append(current.strftime("%Y%m"))
        # Move to next month
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)

    return months


def main():
    parser = argparse.ArgumentParser(description="Download LTA OD data")
    parser.add_argument("--start", default="202001", help="Start month YYYYMM (default: 202001)")
    parser.add_argument("--end", default="202602", help="End month YYYYMM (default: 202602)")
    parser.add_argument("--test", action="store_true", help="Only download latest month as test")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if args.test:
        months = ["202602"]
        print("=== TEST MODE: downloading only 202602 ===")
    else:
        months = generate_months(args.start, args.end)
        print(f"=== Downloading {len(months)} months: {args.start} to {args.end} ===")

    # Track results
    success_count = 0
    fail_count = 0
    skipped_count = 0
    first_available = None
    last_available = None

    for i, ym in enumerate(months, 1):
        print(f"\n[{i}/{len(months)}] {ym}")
        results = download_month(ym)

        # Check if any succeeded
        any_success = any(results.values())
        any_new = False

        for label, success in results.items():
            if success:
                success_count += 1
                if first_available is None:
                    first_available = ym
                last_available = ym
                # Check if file already existed (was skipped)
                csv_name = label.split()[0].lower() + "_" + label.split()[1] + ".csv"
                # Reconstruct filename
                pt_type = label.split()[0]
                csv_file = DATA_DIR / f"origin_destination_{pt_type.lower()}_{ym}.csv"
                if csv_file.exists():
                    pass  # already counted
            else:
                fail_count += 1

        if not any_success:
            print(f"    >>> No data available for {ym} — stopping early <<<")
            break

    # Summary
    print("\n" + "=" * 60)
    print("DOWNLOAD COMPLETE")
    print("=" * 60)
    print(f"  Directory: {DATA_DIR}")
    print(f"  Data range: {first_available} to {last_available}" if first_available else "  No data downloaded")

    # Count files
    bus_files = sorted(DATA_DIR.glob("origin_destination_bus_*.csv"))
    train_files = sorted(DATA_DIR.glob("origin_destination_train_*.csv"))
    print(f"  Bus files:  {len(bus_files)}")
    print(f"  Train files: {len(train_files)}")

    total_size = sum(f.stat().st_size for f in bus_files + train_files) / (1024 ** 3)
    print(f"  Total size: {total_size:.2f} GB")

    if bus_files:
        print(f"  First bus file:  {bus_files[0].name}")
        print(f"  Last bus file:   {bus_files[-1].name}")
    if train_files:
        print(f"  First train file: {train_files[0].name}")
        print(f"  Last train file:  {train_files[-1].name}")


if __name__ == "__main__":
    main()
