import requests
from typing import List
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy


def get_wms_geotiff(
    bbox: List[float],
    output_filepath: str,
    layer: str = "rt_ofc.5k24.32bit",
    width: int = 800,
    height: int = 800,
    crs: str = "EPSG:25832",
    base_url: str = "https://www502.regione.toscana.it/ows_ofc/com.rt.wms.RTmap/wms",
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
        "map": "owsofc_rt",  # Required MapServer map identifier
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetMap",
        "LAYERS": layer,
        "STYLES": "",
        "CRS": crs,
        "BBOX": bbox_str,
        "WIDTH": width,
        "HEIGHT": height,
        "FORMAT": "image/tiff",
        "EXCEPTIONS": "INIMAGE",  # How to report errors
        "TRANSPARENT": "true",
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
        content_type = response.headers.get("Content-Type")

        if "image/tiff" in content_type:
            # Save the image content to the specified file
            with open(output_filepath, "wb") as f:
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


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f"point_{self.x}_{self.y}"


class Tile:
    def __init__(self, point: Point, bbox_step: int = 80, prefix: str = "test_data"):
        self.point = point
        self.bbox_step = bbox_step
        self.prefix = prefix

    def __str__(self):
        return f"{self.point}"

    @property
    def bbox(self):
        return self.coordinates_to_bbox(self.point, self.bbox_step)

    def download(self, output_file: str | None = None):
        if output_file is None:
            output_file = f"{self.point.x}_{self.point.y}.tif"

        get_wms_geotiff(self.bbox, f"{self.prefix}/{output_file}")

    @classmethod
    def coordinates_to_bbox(cls, point: Point, step=80) -> list:
        # min_x = 680012.63 - 250  # 250m to the west
        # min_y = 4849412.92 - 250  # 250m to the south
        # max_x = 680012.63 + 250  # 250m to the east
        # max_y = 4849412.92 + 250  # 250m to the north

        step = step / 2
        return [
            point.x - step,
            point.y - step,
            point.x + step,
            point.y + step,
        ]


def download_florence_tiles(start: Point, end: Point):
    """
    Params:
    start_point: tuple of (x, y) in EPSG:25832, bottom-left corner
    end_point: tuple of (x, y) in EPSG:25832, top-right corner
    """
    step_in_m = 80

    current = deepcopy(start)

    tiles_to_download: list[Tile] = []

    while current.y < end.y:
        while current.x < end.x:
            tiles_to_download.append(Tile(Point(current.x, current.y)))
            current.x = current.x + step_in_m
        current.y = current.y + step_in_m
        current.x = start.x

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(lambda t: t.download(), tiles_to_download)


if __name__ == "__main__":
    start_point = Point(679429.24, 4849095.29)
    end_point = Point(682424.87, 4850207.81)

    download_florence_tiles(start=start_point, end=end_point)
