import os
import shutil
import yaml

def copy_images():

    with open("paths.yaml") as f:
        yaml_file = yaml.safe_load(f)

    src_path = yaml_file["src_path"]
    dst_path = yaml_file["dst_path"]

    for root, dirs, files in os.walk(src_path):
        print(dirs)
        print("Processing ", root.split("\\")[-1])
        for f in files:
            if f.endswith(".JPG"):
                src = os.path.join(root, f)
                dst = os.path.join(dst_path, f)
                shutil.copy2(src, dst)

            
copy_images()