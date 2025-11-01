import xml.etree.ElementTree as ET
import csv
from pathlib import Path


def parse_pascal_voc_xml(xml_path):
    """
    Parse a Pascal VOC XML file and extract annotations.
    
    Args:
        xml_path: Path to the XML file
        
    Returns:
        List of dictionaries containing annotation data
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Get the filename
    filename = root.find('filename').text
    
    annotations = []
    
    # Iterate through all objects in the XML
    for obj in root.findall('object'):
        # Get the label name
        label = obj.find('name').text
        
        # Get bounding box coordinates
        bndbox = obj.find('bndbox')
        xmin = int(bndbox.find('xmin').text)
        ymin = int(bndbox.find('ymin').text)
        xmax = int(bndbox.find('xmax').text)
        ymax = int(bndbox.find('ymax').text)
        
        annotations.append({
            'image_path': filename,
            'xmin': xmin,
            'ymin': ymin,
            'xmax': xmax,
            'ymax': ymax,
            'label': label
        })
    
    return annotations


def convert_annotations_to_deepforest_csv(annotations_dir, output_csv):
    """
    Convert all Pascal VOC XML annotations to DeepForest CSV format.
    
    Args:
        annotations_dir: Directory containing XML annotation files
        output_csv: Path to output CSV file
    """
    annotations_dir = Path(annotations_dir)
    
    # Get all XML files in the directory
    xml_files = list(annotations_dir.glob('*.xml'))
    
    if not xml_files:
        print(f"No XML files found in {annotations_dir}")
        return
    
    print(f"Found {len(xml_files)} XML files")
    
    # Collect all annotations
    all_annotations = []
    
    for xml_file in xml_files:
        try:
            annotations = parse_pascal_voc_xml(xml_file)
            all_annotations.extend(annotations)
            print(f"Processed {xml_file.name}: {len(annotations)} annotations")
        except Exception as e:
            print(f"Error processing {xml_file.name}: {e}")
    
    # Write to CSV
    if all_annotations:
        with open(output_csv, 'w', newline='') as csvfile:
            fieldnames = ['image_path', 'xmin', 'ymin', 'xmax', 'ymax', 'label']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(all_annotations)
        
        print(f"\nSuccessfully wrote {len(all_annotations)} annotations to {output_csv}")
    else:
        print("No annotations found to write")


if __name__ == "__main__":
    # Define paths
    
    base_path = Path("data/02_processed")
    
    folders = ["train", "evaluate", "test"]
    
    for folder in folders:
        path = base_path / folder
        
        annotations_dir = path / "annotations"
        output_csv = path / "annotations.csv"
    
        # Convert annotations
        convert_annotations_to_deepforest_csv(annotations_dir, output_csv)
    
    print("\nConversion complete!")
