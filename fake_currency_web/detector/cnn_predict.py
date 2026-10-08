import os
import re

import cv2
import numpy as np
import pytesseract
import tensorflow as tf
from tensorflow.keras.preprocessing import image


# =========================
# TESSERACT PATH
# =========================
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# =========================
# LOAD BEST MODEL
# =========================
MODEL_DIR = os.path.dirname(__file__)

MODEL_CANDIDATES = [
    "best_currency_model.keras",
    "currency_model.keras",
    "currency_model.h5",
]

MODEL_PATH = None

for model_name in MODEL_CANDIDATES:
    candidate_path = os.path.join(MODEL_DIR, model_name)
    if os.path.exists(candidate_path):
        MODEL_PATH = candidate_path
        break

if MODEL_PATH is None:
    raise FileNotFoundError("No model found in detector folder")

model = tf.keras.models.load_model(MODEL_PATH)
MODEL_IMAGE_SIZE = tuple(model.input_shape[1:3])


def load_image_safe(img_path):
    return cv2.imread(img_path)


def preprocess(img_path):
    img = image.load_img(img_path, target_size=MODEL_IMAGE_SIZE)
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0
    return img_array


def extract_text(img_path):
    img = load_image_safe(img_path)

    if img is None:
        return ""

    resized = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    resized_gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    denoised = cv2.bilateralFilter(resized_gray, 9, 75, 75)

    otsu = cv2.threshold(
        denoised,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )[1]

    adaptive = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        2,
    )

    inverted = cv2.bitwise_not(otsu)

    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(resized, -1, kernel)

    configs = [
        "--oem 3 --psm 6",
        "--oem 3 --psm 11",
        "--oem 3 --psm 12",
    ]

    images = [
        img,
        resized,
        gray,
        resized_gray,
        denoised,
        otsu,
        adaptive,
        inverted,
        sharpened,
    ]

    texts = []

    for ocr_img in images:
        for config in configs:
            try:
                texts.append(pytesseract.image_to_string(ocr_img, config=config))
            except pytesseract.TesseractError:
                pass

    return "\n".join(texts).upper()


def extract_serial_number(text):
    text = text.upper()
    text = re.sub(r"[^A-Z0-9]", "", text)

    patterns = [
        r"\d[A-Z]{2}\d{6}",
        r"[A-Z]{1,3}\d{6,9}",
        r"\d{2}[A-Z]{2}\d{6}",
        r"[A-Z]\d{7,9}",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group()

    return "Not Detected"


def detect_currency_value(text):
    text = text.upper()
    compact_text = re.sub(r"\s+", " ", text)

    word_patterns = {
        "2000": [r"\bTWO\s+THOUSAND\b"],
        "500": [r"\bFIVE\s+HUNDRED\b"],
        "200": [r"\bTWO\s+HUNDRED\b"],
        "100": [r"\bONE\s+HUNDRED\b"],
        "50": [r"\bFIFTY\b"],
        "20": [r"\bTWENTY\b"],
        "10": [r"\bTEN\b", r"\bDAS\b"],
    }

    values = ["2000", "500", "200", "100", "50", "20", "10"]
    scores = {value: 0 for value in values}

    for value in values:
        strong_patterns = [
            rf"(?:₹|â‚¹|\$|RS\.?|INR)\s*{value}\b",
            rf"\b{value}\s*(?:RUPEES?|RUPAYE|RS\.?|INR)\b",
            rf"\b{value}/-",
        ]
        ocr_rupee_patterns = []

        if value == "10":
            ocr_rupee_patterns = [
                rf"\b[SZ]\s*{value}\b",
            ]
        standalone_patterns = [
            rf"(?<!\d){value}(?!\d)",
        ]

        for pattern in strong_patterns:
            scores[value] += 5 * len(re.findall(pattern, compact_text))

        for pattern in ocr_rupee_patterns:
            scores[value] += 4 * len(re.findall(pattern, compact_text))

        for pattern in word_patterns[value]:
            scores[value] += 4 * len(re.findall(pattern, compact_text))

        for pattern in standalone_patterns:
            scores[value] += len(re.findall(pattern, compact_text))

    best_value = max(scores, key=scores.get)

    if scores[best_value] == 0:
        return "Not Detected"

    return best_value


def has_fake_note_text(text):
    fake_patterns = [
        r"\bSPECIMEN\b",
        r"\bCOPY\b",
        r"\bCHILDREN\s+BANK\b",
        r"\bEDUCATIONAL\s+PURPOSE\b",
        r"\bFOR\s+EDUCATIONAL\b",
        r"\bNOT\s+LEGAL\s+TENDER\b",
        r"\bPLAY\s+MONEY\b",
    ]

    return any(re.search(pattern, text.upper()) for pattern in fake_patterns)


def predict_currency(img_path):
    try:
        img_array = preprocess(img_path)

        prediction = model.predict(img_array, verbose=0)
        prediction = np.asarray(prediction)

        if prediction.shape[-1] == 1:
            real_prob = float(prediction[0][0])

            if real_prob >= 0.5:
                result = "Real"
                confidence = round(real_prob * 100, 2)
            else:
                result = "Fake"
                confidence = round((1 - real_prob) * 100, 2)

        else:
            class_names = ["Fake", "Real"]
            class_index = int(np.argmax(prediction[0]))
            result = class_names[class_index]
            confidence = round(float(prediction[0][class_index]) * 100, 2)

        text = extract_text(img_path)

        if has_fake_note_text(text):
            result = "Fake"
            confidence = max(confidence, 95.0)
        elif confidence < 60:
            result = "Uncertain"

        return {
            "result": result,
            "confidence": confidence,
            "country": "India",
            "currency_name": "Indian Rupee",
            "currency_value": detect_currency_value(text),
            "serial_number": extract_serial_number(text),
        }

    except Exception as e:
        return {
            "result": "Error",
            "confidence": 0,
            "country": "India",
            "currency_name": "Indian Rupee",
            "currency_value": "Not Detected",
            "serial_number": "Not Detected",
            "error": str(e),
        }
