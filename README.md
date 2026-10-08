# Indian Fake Currency Detection

A Django web app and CNN code for classifying Indian currency note images.

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.
3. Install Tesseract OCR and update the executable path in `fake_currency_web/detector/cnn_predict.py` if needed.
4. From `fake_currency_web/detector`, run `python restore_model.py` to rebuild the model file from its two uploaded parts.
5. From `fake_currency_web`, run `python manage.py migrate` and then `python manage.py runserver`.

The model is stored in two parts under `fake_currency_web/detector/` to fit GitHub upload limits. Training datasets, user-uploaded media, the local SQLite database, and the virtual environment are excluded from Git because they contain local/generated or potentially private data. Add training data locally under the expected dataset folder before running training scripts.

Set `DJANGO_SECRET_KEY`, `EMAIL_HOST_USER`, and `EMAIL_HOST_PASSWORD` as environment variables for local configuration. Do not commit real credentials.
