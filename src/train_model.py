import torch
from pathlib import Path
from deepforest import main
from pytorch_lightning import Trainer
from pytorch_lightning.callbacks import ModelCheckpoint
from pytorch_lightning.loggers import CSVLogger
from config import load_config

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

    # Loads the training and validation data configuration
    model.config["train"]["csv_file"] = data_config["annotations_file"]
    model.config["train"]["root_dir"] = data_config["processed_data_dir"]
    
    # TODO: Uncomment and set validation data if available,
    # also, find a monitor metric that works well for deepforest
    # model.config["validation"]["csv_file"] = data_config["annotations_file"]
    # model.config["validation"]["root_dir"] = data_config["processed_data_dir"]

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
        callbacks=[checkpoint_callback]
    )

    print("Starting model fine-tuning...")
    trainer.fit(model)

    print("Completed training.")
    print(f"Best model checkpoint saved at: {checkpoint_callback.best_model_path}")

    final_model_path = model_config["final_model_path"]
    print(f"Saving final model to {final_model_path}")
    torch.save(model.model, final_model_path)
    print("Final model saved.")


if __name__ == '__main__':
    train()