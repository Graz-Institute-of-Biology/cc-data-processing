
import os

yaml_files = ["labelbox_gg_june24.yaml",
			        "labelbox_gg_july24.yaml",
					"labelbox_gg_august24.yaml",
					"labelbox_gg_september24.yaml",
                    "labelbox_gg_june25.yaml",
					"labelbox_gg_july0425.yaml",
					"labelbox_gg_july3025.yaml",
					"labelbox_gg_august2625.yaml",
                    "labelbox_gg_octobre1225.yaml"]

project_count = 1
for yaml_file in yaml_files:
    project_code = "01{}".format(project_count)
    project_name = yaml_file.split(".")[0].split("_")[-1]
    img_dir = "C:\\Users\\faulhamm\\Documents\\Philipp\\training\\grossglockner\\{0}_{1}\\imgs".format(project_code, project_name)
    mask_dir = "C:\\Users\\faulhamm\\Documents\\Philipp\\training\\grossglockner\\{0}_{1}\\combined_masks".format(project_code, project_name)

    for file in os.listdir(img_dir):
        if file.endswith(".JPG"):
            already_renamed = len(file.split("_")) == 2
            if already_renamed:
                print(f"File {file} in {img_dir} is already renamed. Skipping.")
                continue

            file_code = file.split(".")[0] + "." + file.split(".")[1][0]
            new_name = file_code + "_" + project_name + ".JPG"
            old_path = os.path.join(img_dir, file)
            new_path = os.path.join(img_dir, new_name)

            os.rename(old_path, new_path)

    for file in os.listdir(mask_dir):
        if file.endswith(".png"):
            already_renamed = len(file.split("_")) == 2
            if already_renamed:
                print(f"File {file} in {mask_dir} is already renamed. Skipping.")
                continue
            file_code = file.split(".")[0] + "." + file.split(".")[1][0]
            new_name = file_code + "_" + project_name + ".png"
            old_path = os.path.join(mask_dir, file)
            new_path = os.path.join(mask_dir, new_name)
            os.rename(old_path, new_path)

    project_count += 1