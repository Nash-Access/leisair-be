# train
from ultralytics import YOLO
from datetime import datetime

#weights=r"F:\uni_work\nash\Weights\yolov8x.pt"
#weights_file = r"F:\uni_work\nash\Weights\yolov8n.pt"
#data=r"F:\uni_work\nash\Dataset\Final yolo.yaml"

'''
Notes:
'Project' parameter is the output folder. 
The new .pt files will be written to root\project\name\weights
In root\project\weights, there will be a load of training metrics that we might not want, so we'll need to look into that

TODO:
Make the log_name a parameter
Make a class for augmentation parameters to pass in to run() 
'''


def run(weights, data, epochs=100):
    log_name = "{}_{}".format(datetime.now().strftime("%Y%m%d%H%M%S"), "100epochAugment19classXmodel")
    model = YOLO(weights)
    model.train(model=weights, data=data,
                epochs=epochs, project=r"TrainingResults", name=log_name,
                degrees=0.2, scale=0.25, perspective=0.0001, fliplr=0.25, erasing=0.1)
    #metrics = model.val()  # run validation, not really any point though because this is real life
