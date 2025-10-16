from pathlib import Path
from deepforest import main
from deepforest import get_data
from deepforest.visualize import plot_results
import matplotlib.pyplot as plt

use_fine_tuned = True

# source = Path("label-studio-export/images/3421ee67-patch_138200_25600.png")
source = Path("all_patches_png/patch_58800_41000.png")


# Load a pretrained tree detection model from Hugging Face


def predict_fine_tuned(source: Path):
    # Load your fine-tuned model from the best checkpoint
    fine_tuned_model = main.deepforest.load_from_checkpoint("models/checkpoints/last.ckpt")
    # fine_tuned_model.config["score_thresh"] = 0.1

    img_fine_tuned = fine_tuned_model.predict_image(path=source)
    plot_results(img_fine_tuned)

def predict_pretrained(source: Path):
    model = main.deepforest()
    model.load_model(model_name="weecology/deepforest-tree", revision="main")
    img_pretrained = model.predict_image(path=source)
    plot_results(img_pretrained)
    
predict_fine_tuned(source=source)