# Cat/Dog Image Classifier

This project contains tools for downloading a dataset of cat/dog images and running a basic image classifier using PyTorch (ResNet18).

## 📂 Project Structure

- `dataset_downloader.py`: Script to fetch images from TheCatAPI and TheDogAPI.
- `cat_dog_predictor.py`: PyTorch inference script using a **pre-trained ResNet50 model** (Zero-Shot).
- `Cats_Dogs/`: Directory containing the downloaded dataset.

## 🚀 Usage

### 1. Download Dataset

Run the downloader script to fetch 50 cats and 50 dogs. The script uses parallel execution for speed.

```bash
python download_dataset.py
```

**Features:**
- Downloads 100 images (50 cats, 50 dogs).
- Uses parallel threads for faster processing.
- Filenames are randomized: `cat-{random_string}.jpg`.
- Skips GIFs/non-static images.

### 2. Run Predictions

You can run the predictor on a single image or an entire folder.

**Predict on a Folder:**
```bash
python cat_dog_predictor.py --folder Cats_Dogs
```

**Predict on a Single Image:**
```bash
python cat_dog_predictor.py --image Cats_Dogs/cat-abc1234567.jpg
```

## 🛠️ Requirements

- Python 3.8+
- PyTorch
- Torchvision
- Pillow
- Requests

Install dependencies:
```bash
pip install torch torchvision pillow requests
```
