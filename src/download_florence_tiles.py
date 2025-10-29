import requests
from typing import List

def get_wms_geotiff(
    bbox: List[float],
    output_filepath: str,
    layer: str = 'rt_ofc.5k24.32bit',
    width: int = 800,
    height: int = 800,
    crs: str = 'EPSG:25832',
    base_url: str = 'https://www502.regione.toscana.it/ows_ofc/com.rt.wms.RTmap/wms'
):
    """
    Downloads a GeoTIFF tile from a WMS service given a bounding box.

    Args:
        bbox (List[float]): The bounding box for the tile in the format
                            [minX, minY, maxX, maxY]. The coordinates must
                            be in the same CRS specified by the 'crs' param.
        output_filepath (str): The path and filename to save the downloaded
                               .tif file (e.g., 'my_tile.tif').
        layer (str, optional): The WMS layer to request.
                               Defaults to 'rt_ofc.5k24.32bit'.
        width (int, optional): The width of the output image in pixels.
                               Defaults to 800.
        height (int, optional): The height of the output image in pixels.
                                Defaults to 800.
        crs (str, optional): The Coordinate Reference System for the BBOX.
                             Defaults to 'EPSG:25832'.
        base_url (str, optional): The base URL of the WMS service.
                                  Defaults to the Regione Toscana service.
    """
    
    # Convert the bounding box list to the comma-separated string
    # required by the WMS BBOX parameter
    bbox_str = ",".join(map(str, bbox))

    # Define all the URL parameters for the GetMap request
    params = {
        'map': 'owsofc_rt',  # Required MapServer map identifier
        'SERVICE': 'WMS',
        'VERSION': '1.3.0',
        'REQUEST': 'GetMap',
        'LAYERS': layer,
        'STYLES': '',
        'CRS': crs,
        'BBOX': bbox_str,
        'WIDTH': width,
        'HEIGHT': height,
        'FORMAT': 'image/tiff',
        'EXCEPTIONS': 'INIMAGE', # How to report errors
        'TRANSPARENT': 'true'
    }

    print(f"Requesting 800x800 GeoTIFF for BBOX: {bbox_str}...")
    
    try:
        # Make the HTTP GET request
        response = requests.get(base_url, params=params)

        # This will raise an exception if the server returns an HTTP error
        # (e.g., 404, 500)
        response.raise_for_status()

        # Check if the server returned a GeoTIFF or an error message
        # WMS errors are often returned as XML or text
        content_type = response.headers.get('Content-Type')
        
        if 'image/tiff' in content_type:
            # Save the image content to the specified file
            with open(output_filepath, 'wb') as f:
                f.write(response.content)
            print(f"Successfully downloaded tile to: {output_filepath}")
        
        else:
            # The server returned something other than a GeoTIFF
            # (likely an error message)
            print("Error: Server did not return a GeoTIFF.")
            print(f"Response Content-Type: {content_type}")
            # Print the error text from the server
            print(f"Server Response (first 500 chars):\n{response.text[:500]}...")

    except requests.exceptions.HTTPError as e:
        # Handle HTTP errors (e.g., 404 Not Found, 500 Internal Server Error)
        print(f"HTTP Error: {e}")
        print(f"Response text: {response.text}")
    except requests.exceptions.RequestException as e:
        # Handle other network-related errors (e.g., connection error)
        print(f"An error occurred: {e}")

# --- Example Usage ---
# This part of the script will only run when you execute it directly
if __name__ == "__main__":
    
    # --- Example 1 ---
    # A 300m x 300m square bounding box we discussed earlier
    # Format: [minX, minY, maxX, maxY]
    bbox_1 = [680400.0, 4849250.0, 680700.0, 4849550.0]
    output_file_1 = "tile_300x300m.tif"
    
    get_wms_geotiff(bbox_1, output_file_1)
    
    print("\n" + "-"*20 + "\n")
    
    # --- Example 2 ---
    # A 500m x 500m square box centered around the coordinate
    # you provided earlier (680012.63, 4849412.92)
    min_x = 680012.63 - 250  # 250m to the west
    min_y = 4849412.92 - 250  # 250m to the south
    max_x = 680012.63 + 250  # 250m to the east
    max_y = 4849412.92 + 250  # 250m to the north
    
    bbox_2 = [min_x, min_y, max_x, max_y]
    output_file_2 = "tile_500x500m_center.tif"
    
    get_wms_geotiff(bbox_2, output_file_2)
