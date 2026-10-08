import joblib
import cv2
import numpy as np

model = joblib.load('../currency_model/currency_model.pkl')
IMG_SIZE = 100

def predict_currency(image_path):
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    img = img.flatten().reshape(1, -1)

    prediction = model.predict(img)[0]
    confidence = max(model.predict_proba(img)[0])

    if prediction == 1:
        return "Genuine", confidence
    else:
        return "Fake", confidence