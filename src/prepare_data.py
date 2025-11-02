import os
from pathlib import Path 
import random

base_path = Path("data/02_processed")
source_images = os.listdir(base_path / "label_studio_export/images")
source_annotations = os.listdir(base_path / "label_studio_export/Annotations")
    

def move_files(annotations, dest):
    
    os.mkdir(dest / "annotations")
    os.mkdir(dest / "images")
    
    for annotation in annotations:
        annotation_name = annotation.split("/")[-1]
        annotation_no_extension = ".".join(annotation_name.split('.')[:-1])
        
        os.rename(base_path / "label_studio_export/Annotations" / annotation, dest / "annotations" / annotation)
        
        image_name = f"{annotation_no_extension}.png"
        if not Path(base_path / "label_studio_export/images" / image_name).exists():
            image_name = f"{annotation_no_extension}.jpg"
        
        
        os.rename(base_path / "label_studio_export/images" / image_name, dest / "images" / image_name)


if __name__ == "__main__":
    
    random.shuffle(source_annotations)
    
    total_annotations = len(source_annotations)
    
    training_percentage = 70
    validation_percentage = 15
    test_percentage = 15
    
    training_number = int(training_percentage * total_annotations / 100)
    validation_number = int(validation_percentage * total_annotations / 100)
    
    print(training_number, validation_number)
    
    training_annotations = source_annotations[:training_number]
    validation_annotations = source_annotations[training_number:training_number+validation_number]
    test_annotations = source_annotations[training_number+validation_number:]
    
    training_dest = base_path / "train"
    validation_dest = base_path / "evaluate"
    test_dest = base_path / "test"
    
    
    for ann, dest in [
        (training_annotations, training_dest),
        (validation_annotations, validation_dest),
        (test_annotations, test_dest),
    ]:
        move_files(ann, dest)
    
    

    
    
    
    
    