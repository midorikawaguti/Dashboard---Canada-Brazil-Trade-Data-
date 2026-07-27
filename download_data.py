# download_data.py
from pathlib import Path
import sys

GDRIVE_FILE_ID = '1R4r91J0yXeSTOTPAl6TqU3P8l8VR-raC'
DATASET_PATH   = Path('Dataset/Dataset.parquet')
MIN_BYTES      = 5_000_000   # valid parquet must be at least 5 MB


def ensure_data():
    """Download parquet from Google Drive if missing or corrupted."""

    if DATASET_PATH.exists():
        size = DATASET_PATH.stat().st_size
        if size >= MIN_BYTES:
            print(f"✅  Dataset ready ({size / 1024 / 1024:.1f} MB)")
            return
        else:
            # Previous download was corrupted — delete and retry
            print(f"⚠️  File exists but is too small ({size} bytes) — removing and re-downloading")
            DATASET_PATH.unlink()

    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading Dataset.parquet from Google Drive...")
    print(f"File ID: {GDRIVE_FILE_ID}")

    import gdown   # guaranteed to be installed via requirements.txt
    url = f'https://drive.google.com/uc?id={GDRIVE_FILE_ID}'
    gdown.download(url, str(DATASET_PATH), quiet=False)

    # Validate
    if not DATASET_PATH.exists():
        raise RuntimeError("Download finished but file not found on disk.")

    size = DATASET_PATH.stat().st_size
    if size < MIN_BYTES:
        DATASET_PATH.unlink()
        raise RuntimeError(
            f"Downloaded file is too small ({size} bytes) — not a valid parquet.\n"
            f"Make sure the file is shared as 'Anyone with the link' in Google Drive.\n"
            f"File ID used: {GDRIVE_FILE_ID}"
        )

    print(f"✅  Dataset downloaded ({size / 1024 / 1024:.1f} MB)")