import torch
import argparse
from pathlib import Path
from deepforest import main
from deepforest.visualize import plot_results
from config import load_config

# Load configuration
config = load_config()
model_config = config["model"]
pred_config = config["prediction"]

def predict(image_path: Path):
    """Load the fine-tuned model and predict on a single image."""
    if not image_path.exists():
        print(f"Error: Image not found at {image_path}")
        return

    print("Loading fine-tuned model...")
    # Create a deepforest model instance
    model = main.deepforest()
    
    # Load the entire fine-tuned pytorch model (not just state dict)
    model.model = torch.load(model_config["final_model_path"], weights_only=False)
    
    # Set the prediction score threshold
    model.config["score_thresh"] = pred_config["score_thresh"]

    print(f"Predicting on {image_path}...")
    img_prediction = model.predict_image(path=str(image_path))
    
    print(f"Found {len(img_prediction)} trees.")
    plot_results(img_prediction)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Predict trees in an image using a fine-tuned model.")
    parser.add_argument("--image_path", required=True, type=Path, help="Path to the image for prediction.")
    args = parser.parse_args()
    
    predict(args.image_path)