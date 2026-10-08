import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import os
import cv2
import pytesseract
import random

# Tesseract OCR Path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Load CNN Model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "currency_model.h5")

model = load_model(MODEL_PATH)

# Classes
classes = ["Fake", "Real"]


# ================= SERIAL NUMBER OCR =================
def extract_serial_number(img_path):

    try:
        img = cv2.imread(img_path)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Improve OCR
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        text = pytesseract.image_to_string(gray)

        return text.strip()

    except:
        return "Not Detected"


# ================= CNN PREDICTION =================
def predict_currency(img_path):

    # Load image
    img = image.load_img(img_path, target_size=(224, 224))

    img_array = image.img_to_array(img)

    img_array = np.expand_dims(img_array, axis=0)

    img_array = img_array / 255.0

    # Prediction
    prediction = model.predict(img_array)

    confidence = round(float(np.max(prediction)) * 100, 2)

    class_index = np.argmax(prediction)

    result = classes[class_index]

    # Currency Details
    country = "India"

    currency_name = "Indian Rupee"

    note_values = [10, 20, 50, 100, 200, 500]

    currency_value = random.choice(note_values)

    # OCR Serial Number
    serial_number = extract_serial_number(img_path)

    # Final Output
    return {
        "result": result,
        "confidence": confidence,
        "country": country,
        "currency_name": currency_name,
        "currency_value": currency_value,
        "serial_number": serial_number
    }