import hashlib
import random
import re
import shutil
from collections import defaultdict
from pathlib import Path


SOURCE_DIR = Path("dataset")
OUTPUT_DIR = Path("dataset_clean")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
RANDOM_SEED = 42
SPLITS = {
    "train": 0.70,
    "validation": 0.15,
    "test": 0.15,
}


def normalize_image_key(path):
    name = path.name.lower()
    name = re.sub(r"^aug_\d+_", "", name)
    name = re.sub(r"\s+-\s+copy", "", name)
    name = re.sub(r"\s*\(\d+\)", "", name)
    name = re.sub(r"[^a-z0-9]+", "", name)
    return name


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_label_and_value(path):
    relative = path.relative_to(SOURCE_DIR)
    parts = relative.parts

    if len(parts) < 4:
        return None

    split, label, value = parts[:3]

    if split not in {"train", "validation", "test"}:
        return None

    if label not in {"real", "fake"}:
        return None

    return label, value


def unique_destination(destination):
    if not destination.exists():
        return destination

    counter = 1
    stem = destination.stem
    suffix = destination.suffix
    parent = destination.parent

    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def main():
    random.seed(RANDOM_SEED)

    if not SOURCE_DIR.exists():
        raise FileNotFoundError(f"Missing dataset folder: {SOURCE_DIR.resolve()}")

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    grouped = defaultdict(dict)

    for path in SOURCE_DIR.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        label_value = get_label_and_value(path)
        if label_value is None:
            continue

        label, value = label_value
        key = (normalize_image_key(path), file_hash(path))

        if key not in grouped[(label, value)]:
            grouped[(label, value)][key] = path

    total_copied = 0

    for (label, value), keyed_paths in sorted(grouped.items()):
        paths = list(keyed_paths.values())
        random.shuffle(paths)

        total = len(paths)
        train_count = int(total * SPLITS["train"])
        validation_count = int(total * SPLITS["validation"])

        split_paths = {
            "train": paths[:train_count],
            "validation": paths[train_count:train_count + validation_count],
            "test": paths[train_count + validation_count:],
        }

        for split, split_files in split_paths.items():
            target_dir = OUTPUT_DIR / split / label / value
            target_dir.mkdir(parents=True, exist_ok=True)

            for source in split_files:
                destination = unique_destination(target_dir / source.name)
                shutil.copy2(source, destination)
                total_copied += 1

        print(
            f"{label}/{value}: total={total}, "
            f"train={len(split_paths['train'])}, "
            f"validation={len(split_paths['validation'])}, "
            f"test={len(split_paths['test'])}"
        )

    print(f"\nCreated clean dataset: {OUTPUT_DIR.resolve()}")
    print(f"Copied unique images: {total_copied}")


if __name__ == "__main__":
    main()
