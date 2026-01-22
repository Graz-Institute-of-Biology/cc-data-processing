import json
import os

img_base_path = r"C:\Users\faulhamm\Documents\Philipp\training\imgs"
mask_base_path = r"C:\Users\faulhamm\Documents\Philipp\training\labelbox_masks"

img_copy_path = r"C:\Users\faulhamm\Documents\Philipp\training\datasets\ATTO\dataset_v10\imgs"
mask_copy_path = r"C:\Users\faulhamm\Documents\Philipp\training\datasets\ATTO\dataset_v10\labelbox_masks"

# Read the JSON file
with open('Export_project_ATTO_Main_160imgs.ndjson', 'r') as file:
    data = [json.loads(line) for line in file if line.strip()]
    print(data)
    # data = json.load(file)

    # Iterate over all entries and print external_id
    for entry in data:
        img_id = entry["data_row"]["external_id"]
        mask_id = img_id.replace("JPG", "png")

        print("ID:", img_id.split(".")[0])
        print("Copying image...")
        os.system(f'copy "{img_base_path}\\{img_id}" "{img_copy_path}\\{img_id}"')

        print("Copying mask...")
        os.system(f'copy "{mask_base_path}\\{mask_id}" "{mask_copy_path}\\{mask_id}"')
        print("-----")