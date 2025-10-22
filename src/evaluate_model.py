import torch
import argparse
from pathlib import Path
from deepforest import main
from config import load_config
import pandas as pd

# Load configuration
config = load_config()
model_config = config["model"]
data_config = config["data"]
pred_config = config["prediction"]

def evaluate(model_path: Path):
    """Load a fine-tuned model and evaluate it on a test set."""
    if not model_path.exists():
        print(f"Error: Model not found at {model_path}")
        return
    test_annotations_path = Path(data_config["annotations_file"])
    if not test_annotations_path.exists():
        print(f"Error: Test annotations file not found at {test_annotations_path}")
        return

    print(f"Loading fine-tuned model from {model_path}...")
    model = main.deepforest()
    model.model = torch.load(model_path, weights_only=False)
    model.config["score_thresh"] = pred_config["score_thresh"]

    print(f"Evaluating model on test data from {test_annotations_path}...")
    
    # The root_dir should point to the directory where the images for evaluation are.
    # Based on your config, it is data_config["processed_data_dir"]
    results = model.evaluate(
        csv_file=str(test_annotations_path),
        root_dir=data_config["processed_data_dir"]
    )

    print("\nEvaluation Results:")
    print("-------------------")
    
    # The results object from evaluate is a dictionary containing a pandas dataframe
    # See https://deepforest.readthedocs.io/en/latest/evaluate.html
    if "results" in results and not results["results"].empty:
        print(results["results"])
    else:
        print("No evaluation results were generated. The test set might be empty or paths might be incorrect.")

    if "box_recall" in results and "box_precision" in results:
        print(f"\nBox Recall: {results['box_recall']:.3f}")
        print(f"Box Precision: {results['box_precision']:.3f}")
    else:
        print("\nCould not calculate box recall and precision.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Evaluate a fine-tuned model.")
    parser.add_argument("--model_path", required=True, type=Path, help="Path to the fine-tuned model file (.pt).")
    # parser.add_argument("--test_annotations", required=True, type=Path, help="Path to the CSV file with test annotations.")
    args = parser.parse_args()
    
    evaluate(args.model_path)#, args.test_annotations)
