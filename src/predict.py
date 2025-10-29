from geopandas import GeoDataFrame
import torch
import argparse
from pathlib import Path
from deepforest import main
from deepforest.visualize import plot_results
from config import load_config
import rasterio
from rasterio.warp import transform as rio_transform
from typing import List, Tuple

# Load configuration
config = load_config()
model_config = config["model"]
pred_config = config["prediction"]


def extract_tree_coordinates_from_prediction(
    image_path: Path, predictions: GeoDataFrame
) -> List[Tuple[float, float]]:
    """
    Extract geographic coordinates for detected trees from predictions in WGS 84 (EPSG:4326).

    Args:
        image_path: Path to the GeoTIFF image file
        predictions: GeoDataFrame containing bounding box predictions with columns:
                     xmin, ymin, xmax, ymax (in pixel coordinates)

    Returns:
        List of tuples (longitude, latitude) representing WGS 84 coordinates of tree centers
    """
    coordinates = []

    with rasterio.open(image_path) as src:
        # Get the affine transform (converts pixel coordinates to geographic coordinates)
        transform = src.transform
        source_crs = src.crs

        print(f"Debug - Transform: {transform}")
        print(f"Debug - Source CRS: {source_crs}")
        print(f"Debug - Bounds: {src.bounds}")

        # Process each prediction
        for idx, pred in predictions.iterrows():
            # Calculate center point of bounding box in pixel coordinates
            center_col = pred["xmin"] + (pred["xmax"] - pred["xmin"]) / 2
            center_row = pred["ymin"] + (pred["ymax"] - pred["ymin"]) / 2

            # Convert pixel coordinates to source CRS geographic coordinates
            # The * operator applies the affine transform: (geo_x, geo_y) = transform * (col, row)
            geo_x, geo_y = transform * (center_col, center_row)

            # Transform from source CRS to WGS 84 (EPSG:4326)
            lon, lat = rio_transform(source_crs, "EPSG:4326", [geo_x], [geo_y])

            if idx == 0:  # Debug first prediction
                print(
                    f"Debug - First prediction pixel coords: col={center_col}, row={center_row}"
                )
                print(
                    f"Debug - First prediction source CRS coords: x={geo_x}, y={geo_y}"
                )
                print(
                    f"Debug - First prediction WGS 84 coords: lon={lon[0]}, lat={lat[0]}"
                )

            coordinates.append((lon[0], lat[0]))

    return coordinates


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

    # Extract geographic coordinates
    tree_coordinates = extract_tree_coordinates_from_prediction(
        image_path, img_prediction
    )
    print("\nTree coordinates (WGS 84 - EPSG:4326):")
    for i, (lon, lat) in enumerate(tree_coordinates, 1):
        print(f"  Tree {i}: ({lat:.10f},{lon:.10f})")

    plot_results(img_prediction)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Predict trees in an image using a fine-tuned model."
    )
    parser.add_argument(
        "--image_path",
        required=True,
        type=Path,
        help="Path to the image for prediction.",
    )
    args = parser.parse_args()

    predict(args.image_path)
