import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
import os
import argparse
from torchvision import models
import numpy as np

class CatDogPredictor:
    def __init__(self, model_path=None):
        """
        Initialize the Cat/Dog predictor.
        
        Args:
            model_path (str): Path to a pre-trained model (optional)
        """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Using device: {self.device}")
        
        # Define image transformations
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        
        # Load model
        if model_path and os.path.exists(model_path):
            self.model = self.load_custom_model(model_path)
        else:
            self.model = self.load_pretrained_model()
        
        self.model.eval()
        self.classes = ['cat', 'dog']
    
    def load_pretrained_model(self):
        """
        Load a pre-trained ResNet model and modify it for binary classification.
        """
        # Load pre-trained ResNet18
        model = models.resnet18(pretrained=True)
        
        # Freeze all layers except the final layer
        for param in model.parameters():
            param.requires_grad = False
        
        # Modify the final layer for binary classification (cat vs dog)
        num_features = model.fc.in_features
        model.fc = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(num_features, 2)  # 2 classes: cat, dog
        )
        
        return model.to(self.device)
    
    def load_custom_model(self, model_path):
        """
        Load a custom trained model from file.
        """
        model = models.resnet18(pretrained=False)
        num_features = model.fc.in_features
        model.fc = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(num_features, 2)
        )
        
        # Load the trained weights
        model.load_state_dict(torch.load(model_path, map_location=self.device))
        return model.to(self.device)
    
    def preprocess_image(self, image_path):
        """
        Preprocess the image for prediction.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            torch.Tensor: Preprocessed image tensor
        """
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.transform(image)
            image_tensor = image_tensor.unsqueeze(0)  # Add batch dimension
            return image_tensor.to(self.device)
        except Exception as e:
            print(f"Error preprocessing image {image_path}: {e}")
            return None
    
    def predict(self, image_path):
        """
        Predict whether the image contains a cat or dog.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            tuple: (prediction, confidence, class_name)
        """
        # Preprocess image
        image_tensor = self.preprocess_image(image_path)
        if image_tensor is None:
            return None, None, None
        
        # Make prediction
        with torch.no_grad():
            outputs = self.model(image_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probabilities, 1)
            
            # Get prediction details
            prediction = predicted.item()
            confidence_score = confidence.item()
            class_name = self.classes[prediction]
            
            return prediction, confidence_score, class_name
    
    def predict_batch(self, image_paths):
        """
        Predict multiple images at once.
        
        Args:
            image_paths (list): List of image file paths
            
        Returns:
            list: List of prediction results
        """
        results = []
        
        for image_path in image_paths:
            if os.path.exists(image_path):
                prediction, confidence, class_name = self.predict(image_path)
                results.append({
                    'image_path': image_path,
                    'prediction': prediction,
                    'confidence': confidence,
                    'class_name': class_name
                })
            else:
                print(f"Image file not found: {image_path}")
                results.append({
                    'image_path': image_path,
                    'prediction': None,
                    'confidence': None,
                    'class_name': None
                })
        
        return results

def main():
    parser = argparse.ArgumentParser(description='Cat/Dog Image Predictor')
    parser.add_argument('--image', type=str, help='Path to a single image file')
    parser.add_argument('--folder', type=str, help='Path to folder containing images')
    parser.add_argument('--model', type=str, help='Path to custom trained model (optional)')
    parser.add_argument('--extensions', nargs='+', default=['.jpg', '.jpeg', '.png', '.bmp'], 
                       help='Image file extensions to process')
    
    args = parser.parse_args()
    
    # Initialize predictor
    predictor = CatDogPredictor(model_path=args.model)
    
    if args.image:
        # Predict single image
        print(f"\nPredicting: {args.image}")
        prediction, confidence, class_name = predictor.predict(args.image)
        
        if prediction is not None:
            print(f"Prediction: {class_name}")
            print(f"Confidence: {confidence:.2%}")
        else:
            print("Failed to predict image")
    
    elif args.folder:
        # Predict all images in folder
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
        
        results = predictor.predict_batch(image_paths)
        
        print(f"\nResults for {len(results)} images:")
        print("-" * 60)
        for result in results:
            if result['prediction'] is not None:
                print(f"{os.path.basename(result['image_path']):<30} | "
                      f"{result['class_name']:<10} | "
                      f"Confidence: {result['confidence']:.2%}")
            else:
                print(f"{os.path.basename(result['image_path']):<30} | "
                      f"Failed to predict")
    
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
            results = predictor.predict_batch(image_paths)
            
            print(f"\nResults for {len(results)} images:")
            print("-" * 60)
            for result in results:
                if result['prediction'] is not None:
                    print(f"{os.path.basename(result['image_path']):<30} | "
                          f"{result['class_name']:<10} | "
                          f"Confidence: {result['confidence']:.2%}")
                else:
                    print(f"{os.path.basename(result['image_path']):<30} | "
                          f"Failed to predict")

if __name__ == "__main__":
    main() 