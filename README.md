# Indian Fake Currency Detection

A student project that combines a Django web app, a CNN image classifier, and OCR helpers to inspect Indian currency note images.

## What it includes

- User registration and login
- Image upload and camera capture for a detection attempt
- CNN output labelled `Real`, `Fake`, or `Uncertain`
- OCR-based currency value and serial-number extraction
- Per-user detection history and an admin dashboard
- Model training and prediction scripts in `currency_model/`

## Important limitations

This is an educational prototype, not a bank, government, or forensic verification tool. A model prediction cannot establish whether a banknote is genuine. Lighting, image quality, note condition, unseen designs, and the training data can affect results. The repository does not include a measured test-set accuracy, so no accuracy claim is made here. Always verify a note through an authorized bank or official process.

OCR values and serial numbers are best-effort text extraction and may be incorrect. The subscription and payment screens are a demo flow; there is no payment gateway or real payment processing.

Uploaded images are saved in the app's local `media/` directory. Use only images you are authorized to process, and do not use real personal or financial information in a public demo.

## Requirements

- Python version compatible with the pinned packages in `requirements.txt`
- Tesseract OCR installed separately
- The model files from this repository

## Setup (Windows PowerShell)

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set a local Django secret key and enable debug mode for local development:

```powershell
$env:DJANGO_SECRET_KEY = python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
$env:DJANGO_DEBUG = "True"
```

Install Tesseract OCR. If it is not at `C:\Program Files\Tesseract-OCR\tesseract.exe`, set `TESSERACT_CMD` to its executable path.

The model is split into two files to fit GitHub's per-file upload limit. From the repository root, rebuild it once:

```powershell
cd fake_currency_web\detector
python restore_model.py
cd ..\..
```

Initialize the database and start the development server:

```powershell
cd fake_currency_web
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in a browser.

## Configuration

`DJANGO_SECRET_KEY` is required. For a deployed environment, set a unique secret key, leave `DJANGO_DEBUG` unset or set it to `False`, and set `DJANGO_ALLOWED_HOSTS` to the deployment host names as a comma-separated list. Never commit secrets.

The `.gitignore` excludes virtual environments, local databases, uploaded media, and both raw and cleaned training datasets. Add authorized training images locally in the folder structure expected by the training scripts; the dataset is not included in this repository.
