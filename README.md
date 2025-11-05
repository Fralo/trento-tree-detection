# Machine Learning Project for Tree Detection

This project uses the DeepForest library to train a model for tree detection in aerial imagery.

## Usage

1.  **Setup Environment**
    ```bash
    pip install -r requirements.txt
    ```

2.  **WIP 🚧 - Prepare Data**
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
    # python src/predict.py --image_path data/02_processed/all_patches_png/patch_58800_41000.png
    ```

## Database Management

### Restore Database from Dump

To restore the PostgreSQL database from a dump file:

```bash
PGPASSWORD=postgres pg_restore -h localhost -p 5432 -U postgres -d trees_db -v -c db_dumps/tree_db_20251104_192751.dump
```

**Parameters:**
- `-h localhost`: Database host
- `-p 5432`: Database port
- `-U postgres`: Database user
- `-d trees_db`: Target database name
- `-v`: Verbose mode
- `-c`: Clean (drop) database objects before recreating them