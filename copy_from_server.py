# copy images from data server to laptop
# find image names from images on laptop (other version) and copy the corresponding images from server to laptop
import os
import shutil

height_dict = {
    'M': 'Main_stem',
    'G': 'Ground',
    'C': 'Canopy'
}

forest_dict = {
    'TF': 'TerraFirme',
    'C': 'Campina',
}

direction_dir = {
    'N': 'North',
    'E': 'East',
    'S': 'South',
    'W': 'West'
}

laptop_img_path = r"C:\Users\faulhamm\Documents\Philipp\Code\cc-machine-learning\results\01-cc-atto\Predictions\TerraFirme\tf_all_classes"
server_base_path = r"Y:\CryptXChange\03_Processed_data\01_Image_data\01_sorted_raw_images"

laptop_target_path = r"C:\Users\faulhamm\Documents\Philipp\Code\cc-machine-learning\results\01-cc-atto\Predictions\TerraFirme\tf_subset"

# get list of image names on laptop
laptop_images = set(os.listdir(laptop_img_path))

to_copy = []
for img_name in laptop_images:
    if img_name.endswith('.JPG'):
        original_img_name = img_name.split('.')[0].split("_no_bg")[0] + ".JPG"  # get base name without extension
        print(original_img_name)
        to_copy.append(original_img_name)


for img_name in to_copy:
    forest_code = img_name.split('_')[1]  # get forest name from image name
    forest = forest_dict.get(forest_code, 'Unknown')  # map forest code to full name
    height_code = img_name.split('_')[2]  # get height code (M, G, C)
    height = height_dict.get(height_code, 'Unknown')  # map height code to full name
    direction_code = img_name.split('_')[3]  # get direction code (N, E, S, W)
    direction = direction_dir.get(direction_code, 'Unknown')  # map direction code to full name
    server_img_path = os.path.join(server_base_path, forest, height, direction, img_name)
    # print(f"Copying {server_img_path} to {laptop_target_path}")

    # if height_code == 'C' or height_code == 'G':
    try:
        shutil.copy(server_img_path, laptop_target_path)
    except Exception as e:
        print(f"Error copying {server_img_path}: {e}")