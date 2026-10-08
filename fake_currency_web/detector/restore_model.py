from pathlib import Path

model_dir = Path(__file__).resolve().parent
parts = sorted(model_dir.glob("best_currency_model.keras.part*"))
if not parts:
    raise FileNotFoundError("Model parts are missing")

model_path = model_dir / "best_currency_model.keras"
with model_path.open("wb") as model_file:
    for part in parts:
        with part.open("rb") as part_file:
            while chunk := part_file.read(1024 * 1024):
                model_file.write(chunk)
print(f"Restored {model_path.name}")
