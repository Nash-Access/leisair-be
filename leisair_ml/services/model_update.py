# train
import base64
from io import BytesIO
import os
import shutil
import re
import torch
from ultralytics import YOLO
from datetime import datetime
from leisair_ml.schemas import BBOX, VesselCorrections
from PIL import Image
from leisair_ml.utils.mongo_handler import MongoDBHandler

#weights=r"F:\uni_work\nash\Weights\yolov8x.pt"
#weights_file = r"F:\uni_work\nash\Weights\yolov8n.pt"
#data=r"F:\uni_work\nash\Dataset\Final yolo.yaml"

mongo_handler = MongoDBHandler()

vessel_classes = ['SUP','Kayak Or Canoe','Rowing Boat','Yacht','Sailing Dinghy','Narrow Boat','Uber Boat',' Class V Passenger','RIB','RNLI','Pleasure Boat', 'Small Powered','Workboat','Tug','Tug - Towing', 'Tug - Pushing','Large Shipping','Fire','Police']

vessel_class_map = {vessel_class: index for index, vessel_class in enumerate(vessel_classes)}

DATASET_PATH = os.getenv("DATASET_PATH", "C:/Users/ayman/OneDrive - Brunel University London/PhD/NASH Project/mount-dir/dataset")
MODEL_PATH = os.getenv("MODEL_PATH", "C:/Users/ayman/OneDrive - Brunel University London/PhD/NASH Project/mount-dir/model")
print(DATASET_PATH)

def generate_yaml_config(path, train_path, val_path, num_classes, class_names):
    """
    Generate a YAML configuration file for Ultralytics YOLOv5 or YOLOv8 model training.

    Args:
        path (str): The directory where the project is located.
        train_path (str): The path to the training dataset.
        val_path (str): The path to the validation dataset.
        num_classes (int): The number of classes to detect.
        class_names (list): A list of class names corresponding to the object classes.

    Returns:
        str: The YAML configuration as a string.
    """
    yaml_config = f"path: {path}\ntrain: {train_path}\nval: {val_path}\nnc: {num_classes}\nnames: {class_names}"
    return yaml_config

def convert_bbox(x1, y1, x2, y2, img_width, img_height):
    """
    Convert bounding box coordinates from (x1, y1, x2, y2) format to YOLOv8 format.

    Args:
        x1 (float): The x-coordinate of the top-left corner of the bounding box.
        y1 (float): The y-coordinate of the top-left corner of the bounding box.
        x2 (float): The x-coordinate of the bottom-right corner of the bounding box.
        y2 (float): The y-coordinate of the bottom-right corner of the bounding box.
        img_width (int): The width of the image.
        img_height (int): The height of the image.

    Returns:
        list: A list containing the converted bounding box in YOLOv8 format [x_center, y_center, width, height].
    """
    # Calculate the width and height of the bounding box
    bbox_width = x2 - x1
    bbox_height = y2 - y1

    # Calculate the center coordinates of the bounding box
    x_center = (x1 + x2) / 2
    y_center = (y1 + y2) / 2

    # Normalize the coordinates to be between 0 and 1
    x_center /= img_width
    y_center /= img_height
    bbox_width /= img_width
    bbox_height /= img_height

    # Return the converted bounding box in YOLOv8 format
    return [x_center, y_center, bbox_width, bbox_height]

def save_training_image(correction: VesselCorrections):
    """
    Calculate the label for a vessel correction and save it to the training dataset.
    """ 
    # Load the image from the base64-encoded string
    print("saving image to dataset", correction.filename)
    image_data = re.sub('^data:image/.+;base64,', '',correction.image)
    image_data = base64.b64decode(image_data)
    image = Image.open(BytesIO(image_data))
    img_width, img_height = image.size
    image_name = f"{correction.filename}_{correction.frame}"
    # Convert the bounding box to YOLOv8 format
    bbox = convert_bbox(correction.bbox.x1, correction.bbox.y1, correction.bbox.x2, correction.bbox.y2, img_width, img_height)

    type_index = vessel_class_map[correction.type] if correction.type in vessel_class_map else ' '
    # Create the label for the vessel correction
    label = f"{type_index} {' '.join(map(str, bbox))}" if type_index != ' ' else ' '

    # Save the label to the training dataset
    with open(f"{DATASET_PATH}/labels/{image_name}.txt", "a") as file:
        file.write(label)

    image.save(f"{DATASET_PATH}/images/{image_name}.jpg")

    if correction.id:
        mongo_handler.update_vessel_correction_to_used(correction.id)

    return label

def compile_training_data():
    vessel_corrections = mongo_handler.get_all_vessel_corrections()
    [save_training_image(correction) for correction in vessel_corrections if correction.used == False or correction.used == None]


def run_training(weights, data, epochs=100, save_dir=None, weights_name=None):
    """
    Run the training process for the Ultralytics YOLOv5 or YOLOv8 model.

    Args:
        weights (str): The path to the initial weights (pre-trained model weights).
        data (str): The path to the YAML configuration file or a dictionary containing the configuration.
        epochs (int, optional): The number of epochs to train for. Default is 100.
        save_dir (str, optional): The directory to save the final model weights. If not provided, the weights will be saved in the default location.

    Returns:
        str: The path to the saved model weights.
    """
    if weights_name:
        log_name = weights_name
    else:
        log_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{epochs}epochAugment{len(data['names'])}classXmodel"

    model = YOLO(weights)
    model.train(model=weights, data=data, epochs=epochs, project=r"TrainingResults", name=log_name,
                degrees=0.2, scale=0.25, perspective=0.0001, fliplr=0.25)

    if save_dir:
        # Get the path to the best.pt file
        best_weights_path = os.path.join("TrainingResults", log_name, "weights", "best.pt")

        # Rename and move the best.pt file to the specified save directory
        new_weights_path = os.path.join(save_dir, f"{log_name}.pt")
        shutil.move(best_weights_path, new_weights_path)

        # Delete the TrainingResults folder
        shutil.rmtree("TrainingResults")

        return new_weights_path
    else:
        return model.get_weights()

def update():
    training_start = datetime.now().strftime('%Y%m_%H%M%S')
    model_id = mongo_handler.insert_new_model(training_start)
    compile_training_data()
    yaml_config = generate_yaml_config(DATASET_PATH, f"{DATASET_PATH}/images", f"{DATASET_PATH}/images", len(vessel_classes), vessel_classes)
    yaml_file = f"{DATASET_PATH}/data.yaml"
    with open(yaml_file, 'w') as file:
        file.write(yaml_config)
    save_weights_dir = f"{MODEL_PATH}"
    try:
        final_weights_path = run_training(f"{MODEL_PATH}/best.pt", yaml_file, epochs=100, save_dir=save_weights_dir, weights_name=str(training_start))
        mongo_handler.upsert_model(model_id, final_weights_path, "trained")
        print("Training complete")
    except Exception as e:
        print(f"Error training model: {e}")
        mongo_handler.update_model_status(model_id, "failed")
        print("Training failed")