"""
Program Name: SegmentationMaskToYolov8
Author: woodsj1206 (https://github.com/woodsj1206)
Description: This program converts a Segmentation mask 1.1 exported from https://app.cvat.ai/ to YOLOv8 Instance Segmentation format. 
Date Created: 5/3/24
Last Modified: 5/4/24
"""
import os
import cv2
import numpy as np

# Open label map file for reading
LABEL_MAP_PATH = input("Enter path of labelmap: ")
labelmap = open(LABEL_MAP_PATH, "r")

# Create dictionary to map RGB colors to class IDs
classes = {}

with labelmap as file:
    next(file) # Skip header information
    next(file) # Skip background color
    
    print("Classes:")
    
    # Iterate over lines in the label map
    for i, line in enumerate(labelmap):
        # Parse the line to extract class name and RGB color
        parsed_line = line.strip().split(":")
        
        # Extract RGB values
        rgb = parsed_line[1].split(",")
        
        # Convert RGB values to tuple of integers
        rgb_tuple = tuple(map(int, rgb))
        
        # Add class id and color tuple to the classes dictionary 
        classes[rgb_tuple] = i
        
        print(f'- {parsed_line[0]}: {i}')

# Directory for segmentation class images
CLASS_DIR = input("Enter path of SegmentationClass: ")

# Directory for segmentation object images
OBJECT_DIR = input("Enter path of SegmentationObject: ")

# Output directory for YOLOv8 labels
OUTPUT_DIR = 'labels'

# Ensure output directory exists, create if it doesn't
os.makedirs(OUTPUT_DIR, exist_ok=True)

# List all files in the object directory
object_files = os.listdir(OBJECT_DIR)

# Iterate over each object file in the directory
for object_file in object_files:
    # Extract file name without extension
    object_image_name = os.path.splitext(object_file)[0]
    
    # Print conversion status
    print(f'Converting: {object_image_name} to YOLOv8 Instance Segmentation Format...')
    
    # Build paths for object and class images
    object_image_path = os.path.join(OBJECT_DIR, object_file)
    class_image_path = os.path.join(CLASS_DIR, object_file)
    
    # Read object and class images
    object_image = cv2.imread(object_image_path)
    class_image = cv2.imread(class_image_path)

    # Find unique colors in the object image
    unique_colors = np.unique(object_image.reshape(-1, object_image.shape[2]), axis=0)
    
    # Open output file for writing YOLOv8 labels
    with open(os.path.join(OUTPUT_DIR, f"{object_image_name}.txt"), 'w') as f:
        # Iterate over unique colors
        for color in unique_colors:
            # Exclude black color ([0, 0, 0])
            if not np.array_equal(color, [0, 0, 0]):
                # Find all pixels with this color in the object image
                class_indices = np.all(object_image == color, axis=-1)
                 
                # Get the corresponding pixel in the class image
                class_pixel = tuple(map(int, class_image[class_indices][0][::-1]))
                
                # Get class ID from the classes dictionary
                class_id = str(classes[class_pixel])
                
                # Extract contours from the mask
                contours, _ = cv2.findContours(class_indices.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Check if any contours are found
                if contours:
                    # Convert contours to polygons
                    polygons = []
                    for cnt in contours:
                        if cv2.contourArea(cnt) > 200:
                            polygon = []
                            for point in cnt:
                                x, y = point[0]
                                polygon.append(x / object_image.shape[1])
                                polygon.append(y / object_image.shape[0])
                            polygons.append(polygon)
                    

                    # Write YOLOv8 instance segmentation format
                    for polygon in polygons:
                        for p_, p in enumerate(polygon):
                            if p_ == len(polygon) - 1:
                                f.write('{}\n'.format(p))
                            elif p_ == 0:
                                f.write('{} {} '.format(class_id, p))
                            else:
                                f.write('{} '.format(p))
                else:
                    # If no contours found, print a message
                    print(f"No contours found for color {color}.")
