import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
import os
import argparse
from torchvision import models
import numpy as np
import concurrent.futures
import threading

# Lock for thread-safe printing
print_lock = threading.Lock()

class CatDogPredictor:
    def __init__(self, model_path=None):
        """
        Initialize the Cat/Dog predictor using Object Detection (Faster R-CNN).
        """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        # If on CPU, we might want to restrict torch threads per process to allow parallelism
        if self.device.type == 'cpu':
           torch.set_num_threads(1)
           
        print(f"Using device: {self.device}")
        
        self.transform = transforms.Compose([
            transforms.ToTensor(),
        ])
        
        self.model = self.load_pretrained_model()
        self.model.eval()
        self.model.share_memory() # crucial for sharing across threads/processes if needed, though threads share anyway
        
        # COCO classes for Faster R-CNN
        # 17: cat, 18: dog (Standard COCO 91-class index)
        self.target_classes = {17: 'cat', 18: 'dog'}
    
    def load_pretrained_model(self):
        """
        Load a pre-trained Faster R-CNN model.
        """
        from torchvision.models.detection import fasterrcnn_resnet50_fpn, FasterRCNN_ResNet50_FPN_Weights
        
        # Load pre-trained model on COCO
        weights = FasterRCNN_ResNet50_FPN_Weights.DEFAULT
        model = fasterrcnn_resnet50_fpn(weights=weights, box_score_thresh=0.5)
        
        return model.to(self.device)
        
    def preprocess_image(self, image_path):
        """
        Preprocess the image for prediction.
        """
        try:
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.transform(image)
            return image_tensor.to(self.device) # Shape: [C, H, W]
        except Exception as e:
            # print(f"Error preprocessing image {image_path}: {e}")
            return None

    def predict(self, image_path):
        """
        Detect cat or dog in the image.
        """
        image_tensor = self.preprocess_image(image_path)
        if image_tensor is None:
            return None, None, None
        
        # Add batch dimension [1, C, H, W]
        input_tensor = [image_tensor]
        
        with torch.no_grad():
            outputs = self.model(input_tensor)
            
        output = outputs[0]
        
        labels = output['labels'].cpu().numpy()
        scores = output['scores'].cpu().numpy()
        
        best_score = 0.0
        best_label = None
        
        for label, score in zip(labels, scores):
            if label in self.target_classes:
                if score > best_score:
                    best_score = score
                    best_label = self.target_classes[label]
        
        if best_label:
            return 0 if best_label == 'cat' else 1, float(best_score), best_label
        else:
            return None, 0.0, "No animal found"

def process_image_wrapper(args):
    """
    Wrapper function for parallel execution.
    args: (predictor, image_path, index, total)
    """
    predictor, image_path, idx, total = args
    
    if os.path.exists(image_path):
        try:
            prediction, confidence, class_name = predictor.predict(image_path)
            
            with print_lock:
                status = f"[{idx}/{total}]"
                filename = os.path.basename(image_path)
                
                if prediction is not None:
                    print(f"{status:<10} {filename:<30} | {class_name.upper():<10} | Conf: {confidence:.2%}")
                else:
                    print(f"{status:<10} {filename:<30} | NO DETECTION")
        except Exception as e:
            with print_lock:
                 print(f"Error processing {os.path.basename(image_path)}: {e}")
    else:
        with print_lock:
             print(f"Image not found: {image_path}")

def main():
    parser = argparse.ArgumentParser(description='Cat/Dog Image Predictor')
    parser.add_argument('--image', type=str, help='Path to a single image file')
    parser.add_argument('--folder', type=str, help='Path to folder containing images')
    parser.add_argument('--model', type=str, help='Path to custom trained model (optional)')
    parser.add_argument('--extensions', nargs='+', default=['.jpg', '.jpeg', '.png', '.bmp'], 
                       help='Image file extensions to process')
    # Removed batch-size argument as requested
    
    args = parser.parse_args()
    
    # Initialize predictor
    predictor = CatDogPredictor(model_path=args.model)
    
    if args.image:
        print(f"\nPredicting: {args.image}")
        prediction, confidence, class_name = predictor.predict(args.image)
        
        if prediction is not None:
            print(f"Prediction: {class_name}")
            print(f"Confidence: {confidence:.2%}")
        else:
            print("Failed to predict image")
    
    elif args.folder:
        print(f"\nPredicting images in folder: {args.folder}")
        
        image_paths = []
        for ext in args.extensions:
            image_paths.extend([
                os.path.join(args.folder, f) for f in os.listdir(args.folder)
                if f.lower().endswith(ext)
            ])
        
        if not image_paths:
            print("No images found in the specified folder")
            return
            
        print(f"\nProcessing {len(image_paths)} images in parallel...")
        print("-" * 60)
        
        # Prepare arguments for parallel processing
        tasks = []
        for i, path in enumerate(image_paths, 1):
            tasks.append((predictor, path, i, len(image_paths)))
        
        # Use ThreadPoolExecutor for parallel processing
        # Adjust max_workers based on CPU cores or preference
        max_workers = min(32, os.cpu_count() + 4) 
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(process_image_wrapper, tasks)
    
    else:
        # Interactive mode
        print("Cat/Dog Image Predictor")
        print("Enter image paths (one per line, press Enter twice to finish):")
        
        image_paths = []
        while True:
            path = input().strip()
            if not path:
                break
            image_paths.append(path)
        
        if image_paths:
             print(f"\nProcessing {len(image_paths)} images...")
             for i, path in enumerate(image_paths, 1):
                prediction, confidence, class_name = predictor.predict(path)
                filename = os.path.basename(path)
                if prediction is not None:
                     print(f"{filename:<30} | {class_name.upper():<10} | Conf: {confidence:.2%}")
                else:
                     print(f"{filename:<30} | NO DETECTION")

if __name__ == "__main__":
    main()