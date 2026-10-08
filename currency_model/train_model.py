import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    Conv2D,
    MaxPooling2D,
    Flatten,
    Dense,
    Dropout,
    BatchNormalization
)
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.utils.class_weight import compute_class_weight
import numpy as np


# =====================================================
# DATASET PATHS
# =====================================================
train_path = "dataset_clean/train"
validation_path = "dataset_clean/validation"
test_path = "dataset_clean/test"
IMG_SIZE = (128, 128)


# =====================================================
# IMAGE PREPROCESSING
# =====================================================
train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=8,
    zoom_range=0.15,
    width_shift_range=0.08,
    height_shift_range=0.08,
    brightness_range=[0.85, 1.15]
)

validation_datagen = ImageDataGenerator(rescale=1./255)
test_datagen = ImageDataGenerator(rescale=1./255)


# =====================================================
# TRAIN GENERATOR
# =====================================================
train_generator = train_datagen.flow_from_directory(
    train_path,
    target_size=IMG_SIZE,
    batch_size=32,
    class_mode="binary",
    shuffle=True
)


# =====================================================
# VALIDATION GENERATOR
# =====================================================
validation_generator = validation_datagen.flow_from_directory(
    validation_path,
    target_size=IMG_SIZE,
    batch_size=32,
    class_mode="binary",
    shuffle=False
)


# =====================================================
# TEST GENERATOR
# =====================================================
test_generator = test_datagen.flow_from_directory(
    test_path,
    target_size=IMG_SIZE,
    batch_size=32,
    class_mode="binary",
    shuffle=False
)


# =====================================================
# CHECK CLASS LABELS
# =====================================================
print("\nCLASS INDICES:")
print(train_generator.class_indices)
print("\n")


# =====================================================
# CLASS WEIGHTS
# =====================================================
class_weights = compute_class_weight(
    class_weight="balanced",
    classes=np.unique(train_generator.classes),
    y=train_generator.classes
)

class_weights = dict(enumerate(class_weights))

print("CLASS WEIGHTS:")
print(class_weights)
print("\n")


# =====================================================
# CNN MODEL
# =====================================================
model = Sequential()

model.add(Conv2D(32, (3, 3), activation="relu", input_shape=(*IMG_SIZE, 3)))
model.add(BatchNormalization())
model.add(MaxPooling2D(pool_size=(2, 2)))

model.add(Conv2D(64, (3, 3), activation="relu"))
model.add(BatchNormalization())
model.add(MaxPooling2D(pool_size=(2, 2)))

model.add(Conv2D(128, (3, 3), activation="relu"))
model.add(BatchNormalization())
model.add(MaxPooling2D(pool_size=(2, 2)))

model.add(Flatten())

model.add(Dense(128, activation="relu"))
model.add(Dropout(0.5))

model.add(Dense(1, activation="sigmoid"))


# =====================================================
# COMPILE MODEL
# =====================================================
model.compile(
    optimizer="adam",
    loss="binary_crossentropy",
    metrics=["accuracy"]
)


# =====================================================
# CALLBACKS
# =====================================================
early_stop = EarlyStopping(
    monitor="val_loss",
    patience=4,
    restore_best_weights=True
)

checkpoint = ModelCheckpoint(
    "best_currency_model.keras",
    monitor="val_accuracy",
    save_best_only=True
)


# =====================================================
# TRAIN MODEL
# =====================================================
history = model.fit(
    train_generator,
    validation_data=validation_generator,
    epochs=15,
    callbacks=[early_stop, checkpoint],
    class_weight=class_weights
)


# =====================================================
# SAVE FINAL MODEL
# =====================================================
model.save("currency_model.keras")
print("\nModel Saved Successfully")


# =====================================================
# ACCURACY GRAPH
# =====================================================
plt.figure(figsize=(8, 5))
plt.plot(history.history["accuracy"])
plt.plot(history.history["val_accuracy"])
plt.title("Model Accuracy")
plt.xlabel("Epoch")
plt.ylabel("Accuracy")
plt.legend(["Train", "Validation"])
plt.grid(True)
plt.show()


# =====================================================
# LOSS GRAPH
# =====================================================
plt.figure(figsize=(8, 5))
plt.plot(history.history["loss"])
plt.plot(history.history["val_loss"])
plt.title("Model Loss")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.legend(["Train", "Validation"])
plt.grid(True)
plt.show()


# =====================================================
# TEST EVALUATION
# =====================================================
test_loss, test_accuracy = model.evaluate(test_generator)

print("\nTEST RESULT:")
print(f"Test Loss: {test_loss:.4f}")
print(f"Test Accuracy: {test_accuracy:.4f}")


# =====================================================
# CONFUSION MATRIX ON TEST DATA
# =====================================================
Y_pred = model.predict(test_generator)

y_pred = (Y_pred > 0.5).astype(int).ravel()
y_true = test_generator.classes

print("\nTEST CLASS INDICES:")
print(test_generator.class_indices)

print("\nCLASSIFICATION REPORT:")
print(
    classification_report(
        y_true,
        y_pred,
        target_names=["Fake", "Real"]
    )
)

cm = confusion_matrix(y_true, y_pred)

plt.figure(figsize=(6, 5))
sns.heatmap(
    cm,
    annot=True,
    fmt="d",
    cmap="Blues",
    xticklabels=["Fake", "Real"],
    yticklabels=["Fake", "Real"]
)

plt.title("Confusion Matrix - Test Data")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.show()