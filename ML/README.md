# Cat/Dog Image Classifier

# Cat/Dog Image Predictor (Object Detection)

This project provides tools for downloading a dataset of cat/dog images and runs a high-performance **Object Detection** pipeline using PyTorch (**Faster R-CNN**).

## 🧠 How It Works

Unlike simple image classifiers (e.g., ResNet18/50) that output a single label for an entire image, this project uses an **Object Detection** model to "see" and locate specific animals within a scene.

### 1. Model Architecture
- **Model**: Faster R-CNN with a ResNet-50-FPN backbone.
- **Pre-training**: Trained on the **COCO** dataset (Common Objects in Context).
- **Inference Strategy**: 
    1. The model scans the image and proposes bounding boxes for potential objects.
    2. It classifies each box into one of 91 COCO categories.
    3. We rigorously filter these detections to only accept **Class 17 (Cat)** and **Class 18 (Dog)**.
    4. If multiple animals are found, the one with the **highest confidence score** is selected as the prediction.

### 2. High-Performance Execution
- **Parallel Processing**: Uses `concurrent.futures.ThreadPoolExecutor` to process images in parallel threads.
- **Latency**: Significantly faster than sequential processing, maximizing CPU/GPU utilization during I/O and inference.

## 📂 Project Structure

- `dataset_downloader.py`: Script to fetch images from TheCatAPI and TheDogAPI.
- `cat_dog_predictor.py`: The main inference script.
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

**Predict on a Folder (Parallel Execution):**
The script automatically uses multiple threads to process images in parallel.
```bash
python cat_dog_predictor.py --folder Cats_Dogs
```

**Predict on a Single Image:**
```bash
python cat_dog_predictor.py --image Cats_Dogs/cat-0vua92y2vv.jpg
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
