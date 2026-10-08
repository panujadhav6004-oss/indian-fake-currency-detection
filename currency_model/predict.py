import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import cv2
import pytesseract
import re

# ==============================
# LOAD MODEL
# ==============================
model = tf.keras.models.load_model("currency_model.keras")

# ==============================
# IMAGE PREPROCESSING (FIXED)
# ==============================
def preprocess(img_path):
    img = image.load_img(img_path, target_size=(128, 128))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0
    return img_array

# ==============================
# OCR IMPROVEMENT (IMPORTANT FIX)
# ==============================
def extract_text(img_path):
    img = cv2.imread(img_path)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # noise removal improves OCR a LOT
    gray = cv2.bilateralFilter(gray, 11, 17, 17)

    text = pytesseract.image_to_string(gray)

    return text.upper()

# ==============================
# VALUE DETECTION (IMPROVED)
# ==============================
def detect_currency_value(text):

    values = ["2000", "500", "200", "100", "50", "20", "10"]

    for v in values:
        if re.search(rf"\b{v}\b", text):
            return f"₹{v}"

    return "Unknown"

# ==============================
# SERIAL NUMBER (IMPROVED)
# ==============================
def extract_serial_number(text):

    # Indian note format is more complex
    patterns = [
        r"\b[A-Z]{2}\s?\d{6,8}\b",
        r"\b[A-Z]{1,2}\d{6,9}\b",
        r"\b\d{2}[A-Z]{2}\d{6}\b"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group().replace(" ", "")

    return "Not Found"

# ==============================
# MAIN PREDICTION (FIXED LOGIC)
# ==============================
def predict_currency(img_path):

    try:
        # MODEL INPUT
        img_array = preprocess(img_path)

        prediction = model.predict(img_array, verbose=0)[0][0]

        # FIXED CLASS LOGIC (IMPORTANT)
        # assume: 0=fake, 1=real

        if prediction >= 0.5:
            result = "Real"
            confidence = prediction * 100
        else:
            result = "Fake"
            confidence = (1 - prediction) * 100

        # OCR
        text = extract_text(img_path)

        # EXTRA INFO
        currency_value = detect_currency_value(text)
        serial_number = extract_serial_number(text)

        return {
            "result": result,
            "confidence": round(confidence, 2),
            "currency_value": currency_value,
            "serial_number": serial_number,
            "country": "India",
            "currency_name": "Indian Rupee"
        }

    except Exception as e:
        return {
            "result": "Error",
            "confidence": 0,
            "currency_value": "Unknown",
            "serial_number": "Unknown",
            "country": "Unknown",
            "currency_name": "Unknown",
            "error": str(e)
        }