#!/usr/bin/env python3
"""
Example usage of the Cat/Dog Image Predictor
"""

from cat_dog_predictor import CatDogPredictor
import os

def example_single_image():
    """Example: Predict a single image"""
    print("=== Single Image Prediction Example ===")
    
    # Initialize predictor
    predictor = CatDogPredictor()
    
    # Example image path (replace with your actual image path)
    image_path = "path/to/your/image.jpg"
    
    if os.path.exists(image_path):
        prediction, confidence, class_name = predictor.predict(image_path)
        
        if prediction is not None:
            print(f"Image: {os.path.basename(image_path)}")
            print(f"Prediction: {class_name}")
            print(f"Confidence: {confidence:.2%}")
        else:
            print("Failed to predict image")
    else:
        print(f"Image file not found: {image_path}")
        print("Please replace with a valid image path")

def example_batch_prediction():
    """Example: Predict multiple images"""
    print("\n=== Batch Prediction Example ===")
    
    # Initialize predictor
    predictor = CatDogPredictor()
    
    # Example image paths (replace with your actual image paths)
    image_paths = [
        "path/to/cat1.jpg",
        "path/to/dog1.jpg",
        "path/to/cat2.jpg",
        "path/to/dog2.jpg"
    ]
    
    # Filter to only existing files
    existing_paths = [path for path in image_paths if os.path.exists(path)]
    
    if existing_paths:
        results = predictor.predict_batch(existing_paths)
        
        print(f"Results for {len(results)} images:")
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
        print("No valid image paths found")
        print("Please replace with valid image paths")

def example_folder_prediction():
    """Example: Predict all images in a folder"""
    print("\n=== Folder Prediction Example ===")
    
    # Initialize predictor
    predictor = CatDogPredictor()
    
    # Example folder path (replace with your actual folder path)
    folder_path = "path/to/your/images/folder"
    
    if os.path.exists(folder_path):
        # Get all image files in the folder
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        image_paths = []
        
        for ext in image_extensions:
            image_paths.extend([
                os.path.join(folder_path, f) for f in os.listdir(folder_path)
                if f.lower().endswith(ext)
            ])
        
        if image_paths:
            results = predictor.predict_batch(image_paths)
            
            print(f"Results for {len(results)} images in folder:")
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
            print("No images found in the specified folder")
    else:
        print(f"Folder not found: {folder_path}")
        print("Please replace with a valid folder path")

if __name__ == "__main__":
    print("Cat/Dog Image Predictor - Example Usage")
    print("=" * 50)
    
    # Run examples
    example_single_image()
    example_batch_prediction()
    example_folder_prediction()
    
    print("\n" + "=" * 50)
    print("Note: Replace the example paths with your actual image/folder paths")
    print("To use from command line:")
    print("  python cat_dog_predictor.py --image path/to/image.jpg")
    print("  python cat_dog_predictor.py --folder path/to/images/")
    print("  python cat_dog_predictor.py  # Interactive mode") 