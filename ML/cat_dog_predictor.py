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
        Load a pre-trained ResNet50 model.
        """
        # Load pre-trained ResNet50 (more accurate than 18)
        # Using the new weights enum if possible, or fallback
        try:
            from torchvision.models import ResNet50_Weights
            model = models.resnet50(weights=ResNet50_Weights.DEFAULT)
            self.weights = ResNet50_Weights.DEFAULT
        except ImportError:
            model = models.resnet50(pretrained=True)
            self.weights = None
            
        return model.to(self.device)
    
    def load_custom_model(self, model_path):
        """
        Load a custom trained model from file.
        """
        model = models.resnet50(pretrained=False)
        # Assuming the custom model was trained with the same binary head architecture
        # If the user provides a model, we assume they know the architecture.
        # But for this 'improve' task, we are likely relying on the pretrained one.
        
        # Re-add binary head only if loading a custom checkpoint that expects it
        num_features = model.fc.in_features
        model.fc = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(num_features, 2)
        )
        model.load_state_dict(torch.load(model_path, map_location=self.device))
        return model.to(self.device)
        
    def get_label_from_index(self, idx):
        """
        Map ImageNet index to Cat or Dog.
        """
        # If we have the weights meta, use it
        if hasattr(self, 'weights') and self.weights:
            categories = self.weights.meta["categories"]
            class_name = categories[idx].lower()
        else:
            # Fallback simple intuitive classes if weights meta missing (older torchvision)
            # This is risky, but standard ImageNet indices are stable.
            pass 
            # Ideally we use the category name. 
            # Let's hope for weights.
            return "Unknown"

        # Simple keyword matching for Cat vs Dog
        # ImageNet has specific breeds.
        
        if 'dog' in class_name or 'terrier' in class_name or 'retriever' in class_name or 'hound' in class_name or 'spaniel' in class_name or 'dane' in class_name or 'shepherd' in class_name or 'collie' in class_name:
            return 'dog', class_name
        elif 'cat' in class_name or 'tabby' in class_name or 'tiger' in class_name or 'siamese' in class_name or 'lynx' in class_name or 'leopard' in class_name or 'jaguar' in class_name or 'lion' in class_name or 'kit' in class_name:
             # filtering out "caterpillar", "catamaran" etc if strictly necessary, but ImageNet classes are usually clear.
             if 'caterpillar' in class_name or 'catamaran' in class_name:
                 return 'other', class_name
             return 'cat', class_name
        else:
            return 'other', class_name

    def preprocess_image(self, image_path):
        """
        Preprocess the image for prediction.
        """
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            # Assuming self.transform is defined in __init__
            image_tensor = self.transform(image)
            image_tensor = image_tensor.unsqueeze(0)  # Add batch dimension
            return image_tensor.to(self.device)
        except Exception as e:
            print(f"Error preprocessing image {image_path}: {e}")
            return None

    def predict(self, image_path):
        """
        Predict whether the image contains a cat or dog.
        """
        # Preprocess image
        image_tensor = self.preprocess_image(image_path)
        if image_tensor is None:
            return None, None, None
        
        # Make prediction
        with torch.no_grad():
            outputs = self.model(image_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            
            # Get top 5 predictions to check for cat/dog presence
            top5_prob, top5_catid = torch.topk(probabilities, 5)
            
            # Check the top 1 first
            top_prob = top5_prob[0][0].item()
            top_catid = top5_catid[0][0].item()
            
            # Map index to label
            if hasattr(self, 'weights') and self.weights:
                categories = self.weights.meta["categories"]
                
                # Check top 1
                label, specific_breed = self.get_label_from_index(top_catid)
                
                # If top 1 is other, check if any of the top 5 are strongly cat or dog?
                # For simplicity, let's stick to top 1, or aggregate.
                
                # Refined logic: If "other", predictions are bad.
                # But since the user only runs this on cats/dogs, we can force a choice between cat/dog probabilities?
                # No, zero-shot is better.
                
                return 0 if label == 'cat' else 1 if label == 'dog' else -1, top_prob, specific_breed
            else:
                 return None, 0, "Error: Old Torchvision"

    def predict_batch(self, image_paths):
        """
        Predict multiple images at once.
        """
        results = []
        
        for image_path in image_paths:
            if os.path.exists(image_path):
                prediction, confidence, class_name = self.predict(image_path)
                
                # Map back to simple class
                simple_class = 'cat' if prediction == 0 else 'dog' if prediction == 1 else 'other'
                
                results.append({
                    'image_path': image_path,
                    'prediction': prediction,
                    'confidence': confidence,
                    'class_name': simple_class,
                    'specific_breed': class_name
                })
            else:
                print(f"Image file not found: {image_path}")
        
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
        
        print("-" * 80)
        for result in results:
            if result['prediction'] is not None:
                breed_info = f"({result['specific_breed']})" if result['specific_breed'] != result['class_name'] else ""
                print(f"{os.path.basename(result['image_path']):<30} | "
                      f"{result['class_name'].upper():<6} {breed_info:<30} | "
                      f"Conf: {result['confidence']:.2%}")
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