from pathlib import Path
from deepforest import main
from pytorch_lightning import Trainer
from pytorch_lightning.loggers import CSVLogger

logger = CSVLogger("logs", name="prova_log")

if __name__ == '__main__':
    # --- 1 load the model ---
    print("Loading pre-trained model...")
    model = main.deepforest()
    model.load_model(model_name="weecology/deepforest-tree", revision="main")


    annotations_file = "deepforest_annotations.csv"

    # the directory where the actual image patches are stored
    root_dir = "label-studio-export/images/"

    annotations_file = Path(annotations_file)


    model.config["train"]["csv_file"] = annotations_file
    model.config["train"]["root_dir"] = Path(root_dir)

    model.trainer = None
    from pytorch_lightning import Trainer
    from pytorch_lightning.callbacks import ModelCheckpoint
    
    # Setup checkpoint callback to save the best model
    checkpoint_callback = ModelCheckpoint(
        dirpath="models/checkpoints",
        filename="best_model-{epoch:02d}-{val_loss:.2f}",
        save_top_k=1,
        monitor="val_loss",
        mode="min",
        save_last=True
    )
    
    trainer = Trainer(
        accelerator="mps",
        devices=model.config["devices"],
        enable_checkpointing=True,
        callbacks=[checkpoint_callback],
        max_epochs=20,
        logger=logger
    )

    # --- 4. training starts ---
    print("Starting model fine-tuning...")
    trainer.fit(model)

    print("Completed training")
    print(f"Best model checkpoint saved at: {checkpoint_callback.best_model_path}")
    print(f"Last model checkpoint saved at: {checkpoint_callback.last_model_path}")