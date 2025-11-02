import torch
from pathlib import Path
from deepforest import main
from pytorch_lightning import Trainer
from pytorch_lightning.callbacks import ModelCheckpoint, Callback
from pytorch_lightning.loggers import CSVLogger
from config import load_config


class CombinedLossLogger(Callback):
    """Custom callback to log combined validation loss."""
    
    def on_validation_epoch_end(self, trainer, pl_module):
        """Calculate and log combined validation loss."""
        # Get the logged metrics
        metrics = trainer.callback_metrics
        
        # Check if validation losses are available
        if "val_classification" in metrics and "val_bbox_regression" in metrics:
            val_class = metrics["val_classification"]
            val_bbox = metrics["val_bbox_regression"]
            
            # Combined loss (you can adjust weights as needed)
            combined_val_loss = val_class + val_bbox
            
            # Log the combined metric
            pl_module.log("val_loss", combined_val_loss, prog_bar=True, logger=True)
            
            # Also log individual components for reference
            pl_module.log("val_loss_classification", val_class, logger=True)
            pl_module.log("val_loss_bbox", val_bbox, logger=True)

# Load configuration
config = load_config()
train_config = config["training"]
model_config = config["model"]
data_config = config["data"]

logger = CSVLogger("logs", name="deepforest_training")

def train():
    print("Loading pre-trained model...")
    model = main.deepforest()
    model.load_model(
        model_name=model_config["pretrained_model_name"],
        revision=model_config["pretrained_model_revision"]
    )

    # Configure training data
    model.config["train"]["csv_file"] = train_config["training_annotations"]
    model.config["train"]["root_dir"] = train_config["training_data"]
    
    # Configure validation data
    model.config["validation"]["csv_file"] = train_config["validation_annotations"]
    model.config["validation"]["root_dir"] = train_config["validation_data"]

    # Initialize callbacks
    combined_loss_logger = CombinedLossLogger()
    
    checkpoint_callback = ModelCheckpoint(
        dirpath=model_config["checkpoint_dir"],
        filename="best_model-{epoch:02d}-{val_loss:.2f}",
        save_top_k=1,
        monitor=train_config["val_loss_monitor"],
        mode="min",
        save_last=True
    )

    trainer = Trainer(
        accelerator=train_config["accelerator"],
        devices=train_config["devices"],
        max_epochs=train_config["max_epochs"],
        logger=logger,
        callbacks=[checkpoint_callback, combined_loss_logger]
    )

    print("Starting model fine-tuning...")
    trainer.fit(model)

    print("Completed training.")
    print(f"Best model checkpoint saved at: {checkpoint_callback.best_model_path}")

    # Save final model with version
    version = logger.version
    final_model_path = Path(model_config["final_model_path"])
    versioned_model_path = final_model_path.with_name(f"{final_model_path.stem}_v{version}{final_model_path.suffix}")
    
    print(f"Saving final model to {versioned_model_path}")
    torch.save(model.model, versioned_model_path)
    print("Final model saved.")


if __name__ == '__main__':
    train()