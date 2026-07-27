#https://drive.google.com/file/d/1R4r91J0yXeSTOTPAl6TqU3P8l8VR-raC/view?usp=drive_link

# download_data.py
import requests
from pathlib import Path

GDRIVE_FILE_ID = 'Y1R4r91J0yXeSTOTPAl6TqU3P8l8VR-raC'
DATASET_PATH   = Path('Dataset/Dataset.parquet')

def ensure_data():
    """Download parquet from Google Drive if not already present."""
    if DATASET_PATH.exists():
        print(f"Dataset already present ({DATASET_PATH.stat().st_size / 1024 / 1024:.1f} MB)")
        return

    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    print("Downloading dataset from Google Drive...")

    url      = f'https://drive.google.com/uc?export=download&id={GDRIVE_FILE_ID}'
    session  = requests.Session()
    response = session.get(url, stream=True)

    # Handle Google's virus-scan warning for large files
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            response = session.get(
                url, params={'confirm': value}, stream=True
            )
            break

    with open(DATASET_PATH, 'wb') as f:
        for chunk in response.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)

    size_mb = DATASET_PATH.stat().st_size / 1024 / 1024
    print(f"✅  Dataset downloaded ({size_mb:.1f} MB)")