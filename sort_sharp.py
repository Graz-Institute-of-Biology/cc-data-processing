import cv2
import numpy as np
import os
import glob
import pandas as pd

def calculate_sharpness(img_path, ind, num_img):
    print("Img {}/{}".format(ind+1, num_img))
    image = cv2.imread(img_path)
    # Convert image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Calculate Laplacian
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    # Calculate sharpness score (variance of Laplacian)
    sharpness = np.var(laplacian)
    return sharpness

# Load images
# Get all jpg files from folder and subfolders
image_paths = glob.glob('E:\Mavic-3-Fotos/**/*.jpg', recursive=True)

# print(image_paths[:50])

# images = [cv2.imread(path) for path in image_paths]
num_img = len(image_paths)

# Calculate sharpness for each image
sharpness_scores = []

for ind, img_path in enumerate(image_paths):
    try:
        sharpness = calculate_sharpness(img_path, ind, num_img)
        sharpness_scores.append(sharpness)
    except:
        print("Error with image {}".format(img_path))
        print("Continuing...")


# Sort images based on sharpness scores
sorted_images = [image for _, image in sorted(zip(sharpness_scores, image_paths), reverse=True)]

# Create a pandas DataFrame with the sorted images and sharpness scores
df = pd.DataFrame({'Image': sorted_images, 'Sharpness Score': sharpness_scores})
df = pd.DataFrame({'Image': sorted_images})

# Save the DataFrame to a CSV file
df.to_csv('sorted_images.csv', index=False)

# Now sorted_images contains your images sorted by sharpness
