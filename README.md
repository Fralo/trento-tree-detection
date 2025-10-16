# Machine Learning Project for Tree Detection

This project uses the DeepForest library to train a model for tree detection in aerial imagery.

## Project Structure

```
.
├── .gitignore          # Specifies intentionally untracked files to ignore
├── README.md           # This file, explaining the project
├── requirements.txt    # Project dependencies
├── config.yml          # Configuration file for paths, and hyperparameters
|
├── data
│   ├── 01_raw          # Immutable raw data (e.g., original TIFs, Label Studio exports)
│   │   └── label-studio-export
│   ├── 02_processed    # Processed data (e.g., PNG patches, annotations CSV)
│   │   ├── all_patches_png
│   │   └── deepforest_annotations.csv
│   └── 03_external     # External data sources
|
├── models              # Trained and serialized models, model predictions
│   ├── checkpoints     # Model checkpoints saved during training
│   └── final_model.pt  # The final, serialized model for inference
|
├── notebooks           # Jupyter notebooks for exploration and analysis
│   └── exploratory_data_analysis.ipynb
|
├── reports             # Generated analysis as HTML, PDF, etc.
│   └── figures         # Generated plots, images, etc.
|
└── src                 # Source code for use in this project
    ├── __init__.py
    ├── config.py       # Script to load and validate configuration
    ├── prepare_data.py # Script to process raw data
    ├── train_model.py  # Script to train the model
    └── predict.py      # Script to run predictions with a trained model
```

## Usage

1.  **Setup Environment**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Prepare Data**
    This script converts raw data into the format required for training.
    ```bash
    python src/prepare_data.py
    ```

3.  **Train Model**
    This script runs the training process using the processed data.
    ```bash
    python src/train_model.py
    ```

4.  **Run Prediction**
    Use the final trained model to make predictions on a new image.
    ```bash
    python src/predict.py --image_path /path/to/your/image.png
    ```