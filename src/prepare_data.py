###
# This script prepares training patches from a large GeoTIFF file
# It splits the raster into smaller patches for training a deep learning model
# The patches are saved to a specified output directory
# TODO -> refactor


from deepforest import get_data
from deepforest.preprocess import split_raster
import os
import logging
import rasterio
from rasterio.windows import Window
import numpy as np
from pathlib import Path
import geopandas as gpd
from shapely.geometry import box

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the path to your large GeoTIFF
geotiff_path = "sources/trento/trento_cropped.tif"

# Define the directory where you want to save the patches
output_dir = "training_patches"

# Create the directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

logger.info(f"Starting processing of {geotiff_path}")

# Check if file exists
if not os.path.exists(geotiff_path):
    logger.error(f"File not found: {geotiff_path}")
    exit(1)

# Get file size and raster info
file_size_mb = os.path.getsize(geotiff_path) / (1024 * 1024)
logger.info(f"File size: {file_size_mb:.2f} MB")

# Patch parameters
patch_size = 800
overlap = 0.25
stride = int(patch_size * (1 - overlap))

# Open raster to get dimensions using rasterio
try:
    with rasterio.open(geotiff_path) as src:
        width = src.width
        height = src.height
        bands = src.count
        logger.info(f"Raster dimensions: {width}x{height} pixels, {bands} bands")
        logger.info(f"CRS: {src.crs}")
        
        # Estimate number of patches
        estimated_patches = ((width // stride) + 1) * ((height // stride) + 1)
        logger.info(f"Estimated patches to create: ~{estimated_patches}")
        
        # Calculate chunk size - process 16000x16000 pixels at a time to limit memory
        chunk_size = 16000
        
except Exception as e:
    logger.error(f"Error reading raster info: {e}")
    exit(1)

logger.info("Starting memory-efficient raster splitting...")
logger.info(f"Processing in {chunk_size}x{chunk_size} chunks to save memory...")

try:
    patch_count = 0
    patches_data = []
    
    with rasterio.open(geotiff_path) as src:
        transform = src.transform
        crs = src.crs
        
        # Process the raster in chunks
        for chunk_row in range(0, height, chunk_size):
            for chunk_col in range(0, width, chunk_size):
                chunk_width = min(chunk_size + patch_size, width - chunk_col)
                chunk_height = min(chunk_size + patch_size, height - chunk_row)
                
                logger.info(f"Processing chunk at ({chunk_col}, {chunk_row}) - size: {chunk_width}x{chunk_height}")
                
                # Read only this chunk
                window = Window(chunk_col, chunk_row, chunk_width, chunk_height)
                chunk_data = src.read(window=window)
                
                # Generate patches within this chunk
                for row in range(0, chunk_height - patch_size + 1, stride):
                    for col in range(0, chunk_width - patch_size + 1, stride):
                        # Extract patch
                        patch = chunk_data[:, row:row+patch_size, col:col+patch_size]
                        
                        # Skip if patch is too small
                        if patch.shape[1] < patch_size or patch.shape[2] < patch_size:
                            continue
                        
                        # Calculate global coordinates
                        global_col = chunk_col + col
                        global_row = chunk_row + row
                        
                        # Save patch
                        patch_filename = f"patch_{global_row}_{global_col}.tif"
                        patch_path = os.path.join(output_dir, patch_filename)
                        
                        # Calculate transform for this patch
                        patch_transform = rasterio.transform.from_bounds(
                            *rasterio.transform.xy(transform, global_row, global_col),
                            *rasterio.transform.xy(transform, global_row + patch_size, global_col + patch_size),
                            patch_size, patch_size
                        )
                        
                        # Write patch
                        with rasterio.open(
                            patch_path,
                            'w',
                            driver='GTiff',
                            height=patch_size,
                            width=patch_size,
                            count=bands,
                            dtype=patch.dtype,
                            crs=crs,
                            transform=patch_transform,
                            compress='lzw'  # Add compression to save disk space
                        ) as dst:
                            dst.write(patch)
                        
                        patch_count += 1
                        
                        if patch_count % 50 == 0:
                            logger.info(f"Created {patch_count} patches so far...")
                            logger.info(f"Estimated completion: {patch_count / estimated_patches * 100:.2f}%")
                
                # Free memory after each chunk
                del chunk_data
                logger.info(f"Completed chunk, {patch_count} total patches created")

    logger.info(f"Successfully created {patch_count} patches in '{output_dir}'.")
    logger.info("Patch creation complete!")
    
except MemoryError:
    logger.error("Out of memory! Try reducing chunk_size further")
except Exception as e:
    logger.error(f"Error during processing: {e}", exc_info=True)