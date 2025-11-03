"""
DeepForest Fine-tuning Script
Fine-tunes the DeepForest model on custom tree detection data.
"""

import os
import argparse
from pathlib import Path
import pandas as pd
from config import load_config
import torch
from deepforest import main
from deepforest import get_data
import matplotlib.pyplot as plt
from pytorch_lightning.callbacks import ModelCheckpoint

config = load_config()
train_config = config["training"]
model_config = config["model"]
data_config = config["data"]

def load_and_validate_data(train_csv, val_csv):
    """
    Load and validate training and validation data.
    
    Expected CSV format:
    image_path, xmin, ymin, xmax, ymax, label
    """
    print("\n" + "="*50)
    print("Loading and validating data...")
    print("="*50)
    
    # Load CSVs
    train_df = pd.read_csv(train_csv)
    val_df = pd.read_csv(val_csv)
    
    # Validate required columns
    required_columns = ['image_path', 'xmin', 'ymin', 'xmax', 'ymax', 'label']
    for col in required_columns:
        if col not in train_df.columns:
            raise ValueError(f"Training CSV missing required column: {col}")
        if col not in val_df.columns:
            raise ValueError(f"Validation CSV missing required column: {col}")
    
    print(f"✓ Training data: {len(train_df)} annotations, {train_df['image_path'].nunique()} images")
    print(f"✓ Validation data: {len(val_df)} annotations, {val_df['image_path'].nunique()} images")
    print(f"✓ Classes: {train_df['label'].unique()}")
    
    return train_df, val_df


def create_model(config):
    """
    Create and configure DeepForest model.
    
    Args:
        config: Dictionary with model configuration
    """
    print("\n" + "="*50)
    print("Creating DeepForest model...")
    print("="*50)
    
    model = main.deepforest()
    
    # Load pretrained weights if specified
    # model.load_model(model_name="weecology/deepforest-tree", revision="main")
    
    # Load pretrained data with old weights 
    model.model = torch.load(
        model_config["final_model_path"],
        weights_only=False
    )
    
    # Configure model
    model.config["train"]["csv_file"] = config['train_csv']
    model.config["train"]["root_dir"] = config.get('train_root_dir', os.path.dirname(config['train_csv']))
    
    model.config["validation"]["csv_file"] = config['val_csv']
    model.config["validation"]["root_dir"] = config.get('val_root_dir', os.path.dirname(config['val_csv']))
    
    # Training hyperparameters
    model.config["batch_size"] = config.get('batch_size', 4)
    model.config["train"]["epochs"] = config.get('epochs', 20)
    model.config["train"]["lr"] = config.get('learning_rate', 0.0001)
    model.config["train"]["scheduler"] = {
        "type": "reduce_on_plateau",
        "monitor": "map",
        "params": {
            "patience": 3,
            "mode": "max",
            "factor": 0.1,
            "threshold": 0.0001,
            "threshold_mode": "rel",
            "cooldown": 1,
            "min_lr": 1e-6,
            "eps": 1e-8
        }
    }
    model.config["score_thresh"] = config.get('score_thresh', 0.4)
    model.config["nms_thresh"] = config.get('nms_thresh', 0.15)
    
    # Set number of workers for data loading
    model.config["workers"] = config.get('num_workers', 4)
    
    print(f"✓ Batch size: {model.config['batch_size']}")
    print(f"✓ Epochs: {model.config['train']['epochs']}")
    print(f"✓ Learning rate: {model.config['train']['lr']}")
    print(f"✓ Score threshold: {model.config['score_thresh']}")
    print(f"✓ NMS threshold: {model.config['nms_thresh']}")
    
    return model


def train_model(model, config):
    """
    Train the DeepForest model.
    
    Args:
        model: DeepForest model instance
        config: Dictionary with training configuration
    """
    print("\n" + "="*50)
    print("Starting training...")
    print("="*50)
    
    # Setup checkpoint callback to save best model
    output_dir = Path(config.get('output_dir', 'models'))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    checkpoint_callback = ModelCheckpoint(
        dirpath=str(output_dir),
        filename='best_model',
        monitor='map',
        mode='max',
        save_top_k=1,
        verbose=True
    )
    
    # Setup trainer arguments
    trainer_args = {
        "fast_dev_run": config.get('fast_dev_run', False),
        "max_epochs": config.get('epochs', 20),
        "callbacks": [checkpoint_callback],
    }
    
    # Add GPU support if available
    if torch.cuda.is_available():
        print(f"✓ Training on GPU: {torch.cuda.get_device_name(0)}")
        trainer_args["accelerator"] = "gpu"
        trainer_args["devices"] = 1
    else:
        print("✓ Training on CPU/MPS")
        trainer_args["accelerator"] = "mps"
    
    # Train the model
    model.create_trainer(**trainer_args)
    model.trainer.fit(model)
    
    print("\n✓ Training completed!")
    print(f"✓ Best model saved to: {checkpoint_callback.best_model_path}")
    
    # Load the best model weights
    best_model_path = checkpoint_callback.best_model_path
    if best_model_path and os.path.exists(best_model_path):
        print(f"✓ Loading best model from: {best_model_path}")
        checkpoint = torch.load(best_model_path)
        model.load_state_dict(checkpoint['state_dict'])
    
    return best_model_path


def evaluate_model(model, config):
    """
    Evaluate the trained model on validation set.
    
    Args:
        model: Trained DeepForest model
        config: Dictionary with evaluation configuration
    """
    print("\n" + "="*50)
    print("Evaluating model...")
    print("="*50)
    
    # Save original batch size and set to 1 for evaluation to avoid collation issues
    # Images may have different sizes, and batch_size > 1 causes tensor stacking errors
    original_batch_size = model.config["batch_size"]
    model.config["batch_size"] = 1
    
    # Run evaluation
    results = model.evaluate(
        csv_file=config['val_csv'],
        root_dir=config.get('val_root_dir', os.path.dirname(config['val_csv'])),
        iou_threshold=config.get('iou_threshold', 0.4)
    )
    
    # Restore original batch size
    model.config["batch_size"] = original_batch_size
    
    print("\nEvaluation Results:")
    print("-" * 50)
    if results is not None:
        for key, value in results.items():
            if isinstance(value, (int, float)):
                print(f"{key}: {value:.4f}")
            else:
                print(f"{key}:")
                print(value)
    
    # Save results
    results_file = Path(config.get('output_dir', 'results')) / 'evaluation_results.txt'
    with open(results_file, 'w') as f:
        f.write("DeepForest Evaluation Results\n")
        f.write("="*50 + "\n")
        if results is not None:
            for key, value in results.items():
                if isinstance(value, (int, float)):
                    f.write(f"{key}: {value:.4f}\n")
                else:
                    f.write(f"{key}:\n{value}\n\n")
    
    print(f"\n✓ Results saved to {results_file}")
    
    return results


def save_model(model, config):
    """
    Save the trained model.
    
    Args:
        model: Trained DeepForest model (already loaded with best weights)
        config: Dictionary with save configuration
    """
    print("\n" + "="*50)
    print("Saving model...")
    print("="*50)
    
    output_dir = Path(config.get('output_dir', 'models'))
    output_dir.mkdir(parents=True, exist_ok=True)

    existing_models = len(os.listdir(output_dir))

    # to save the model with version, not only the default name
    model_path = output_dir / f"deepforest_finetuned_{existing_models}.pt"
    
    # Save model state dict
    torch.save(model.model, model_path)
    
    print(f"✓ Model (best weights) saved to {model_path}")
    if config.get('best_model_path'):
        print(f"✓ PyTorch Lightning checkpoint also available at: {config['best_model_path']}")
    
    # Save configuration
    config_path = output_dir / 'config.txt'
    with open(config_path, 'w') as f:
        f.write("DeepForest Training Configuration\n")
        f.write("="*50 + "\n")
        for key, value in config.items():
            f.write(f"{key}: {value}\n")
    
    print(f"✓ Configuration saved to {config_path}")


def main_pipeline(args):
    """
    Main training pipeline.
    
    Args:
        args: Command line arguments
    """
    print("\n" + "="*70)
    print(" " * 15 + "DeepForest Fine-tuning Pipeline")
    print("="*70)
    
    training_data = train_config["training_data"]
    training_annotations = train_config["training_annotations"]
    validation_data = train_config["validation_data"]
    validation_annotations = train_config["validation_annotations"]

    # Create configuration
    config = {
        'train_csv': training_annotations,
        'val_csv': validation_annotations,
        'train_root_dir': training_data,
        'val_root_dir': validation_data,
        'use_pretrained': args.use_pretrained,
        'batch_size': args.batch_size,
        'epochs': args.epochs,
        'learning_rate': args.learning_rate,
        'score_thresh': args.score_thresh,
        'nms_thresh': args.nms_thresh,
        'num_workers': args.num_workers,
        'output_dir': args.output_dir,
        'model_name': args.model_name,
        'iou_threshold': args.iou_threshold,
        'fast_dev_run': False,
    }
    
    # Load and validate data
    train_df, val_df = load_and_validate_data(training_annotations, validation_annotations)
    
    # Create model
    model = create_model(config)
    
    # Train model (returns path to best model checkpoint)
    best_model_path = train_model(model, config)
    config['best_model_path'] = best_model_path
    
    # Evaluate model (now using best weights)
    # evaluate_model(model, config)
    
    # Save final model with custom name
    save_model(model, config)
    
    print("\n" + "="*70)
    print(" " * 20 + "Pipeline completed successfully!")
    print("="*70 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fine-tune DeepForest model for tree detection",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Data arguments
    
    # Model arguments
    parser.add_argument(
        '--use-pretrained',
        action='store_true',
        default=True,
        help='Use pretrained Bird Detector weights'
    )
    parser.add_argument(
        '--no-pretrained',
        action='store_false',
        dest='use_pretrained',
        help='Train from scratch without pretrained weights'
    )
    
    # Training hyperparameters
    parser.add_argument(
        '--batch-size',
        type=int,
        default=4,
        help='Batch size for training'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=20,
        help='Number of training epochs'
    )
    parser.add_argument(
        '--learning-rate',
        type=float,
        default=0.0001,
        help='Learning rate'
    )
    parser.add_argument(
        '--score-thresh',
        type=float,
        default=0.4,
        help='Score threshold for predictions'
    )
    parser.add_argument(
        '--nms-thresh',
        type=float,
        default=0.15,
        help='NMS threshold for predictions'
    )
    parser.add_argument(
        '--num-workers',
        type=int,
        default=4,
        help='Number of data loading workers'
    )
    
    # Evaluation arguments
    parser.add_argument(
        '--iou-threshold',
        type=float,
        default=0.4,
        help='IoU threshold for evaluation'
    )
    
    # Output arguments
    parser.add_argument(
        '--output-dir',
        type=str,
        default='models',
        help='Directory to save trained model and results'
    )
    parser.add_argument(
        '--model-name',
        type=str,
        default='deepforest_finetuned.pt',
        help='Name for saved model file'
    )
    
    # Debug arguments
    parser.add_argument(
        '--fast-dev-run',
        action='store_true',
        help='Run a quick test with minimal data (for debugging)'
    )
    
    args = parser.parse_args()
    main_pipeline(args)
