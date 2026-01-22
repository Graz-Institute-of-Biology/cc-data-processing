import os
import cv2
import numpy as np
from tqdm import tqdm


def transform_masks(input_folder, output_folder):
    """ Transform mask values (use only bryophytes instead of subclasses)

    Args:
        input_folder (str): input folder path
        output_folder (str): output folder path
    """
    for filename in tqdm(os.listdir(input_folder)):
        if filename.lower().endswith('.png'):
            img_path = os.path.join(input_folder, filename)
            img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        if img is not None:
            img[img > 4] = 1
            out_path = os.path.join(output_folder, filename)
            cv2.imwrite(out_path, img)



def check_image_values(output_folder):

    for img in os.listdir(output_folder):
        img_path = os.path.join(output_folder, img)
        image = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        if image is not None:
            unique_values = np.unique(image)
            print(f"{img}: {unique_values}")


if __name__ == "__main__":
    input_folder = 'C:\\Users\\faulhamm\\Documents\\Philipp\\training\\cc_graz\\saved_datasets\\v1L\\partial_masks'
    output_folder = 'C:\\Users\\faulhamm\\Documents\\Philipp\\training\\cc_graz\\saved_datasets\\v1L\\transformed_masks'
    os.makedirs(output_folder, exist_ok=True)

    transform_masks(input_folder, output_folder)
    check_image_values(output_folder)