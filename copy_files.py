import os
import shutil
import yaml
import pandas as pd
import create_codename as cc
from create_codename import convert_string_to_float
from gps_class import GPSVis
import numpy as np

def calculate_bearing(degree):
    """calculates canonical names from directional degrees: 
    (-45°, 45° = N)
    (45°, 135° = E)
    (135°, 45° = S)
    (-45°, 45° = W)

    Args:
        degree (float): direction in degrees

    Returns:
        string: direction name (N,E,S,W)
    """
    # function from: https://gist.github.com/RobertSudwarts/acf8df23a16afdb5837f
    dirs = ['N', 'E', 'S', 'W']
    ix = int(round(degree / (360. / len(dirs))))
    return dirs[ix % len(dirs)]

def copy_images_from_folder():
        
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


def copy_files_from_csv(csv_file=None, dst_folder=None, max_count=200):
    df = pd.read_csv(csv_file)
    file_paths = df["Image"].tolist()

    tf_count = 0
    c_count = 0
    
    for file_path in file_paths:
        # src = os.path.join(src_path, file_name)
        file_path = file_path.replace('E', 'D', 1)
        file_name = file_path.split("\\")[-1]
        # dst = os.path.join(dst_folder, file_name)
        try:
            results, i = cc.get_img_meta(file_path)
            rel_altitude_string = i.getxmp()['xmpmeta']['RDF']['Description']['RelativeAltitude']
        except Exception as e:
            print("No meta found, skipping...")
            continue
        rel_altitude = convert_string_to_float(rel_altitude_string)

        if "Tree" in file_path.split("\\")[-2] and rel_altitude < 4:
            dst_ext = "\\".join(file_path.split("\\")[3:])
            
            if "Campina" in file_path:
                dst = os.path.join(dst_folder, "C", dst_ext)
                c_count += 1
                print("C")
            else:
                dst = os.path.join(dst_folder, "TF", dst_ext)
                tf_count += 1
                print("TF")

            print(file_name)
            print(dst)
            print(rel_altitude)
            print("-------------------")
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(file_path, dst)
            # data_csv_path = "\\".join(file_path.split("\\")[:-1]) + "\\data.csv"
            # print(data_csv_path)
            # if os.path.isfile(data_csv_path):
            #     shutil.copy2(data_csv_path, dst)

            if tf_count > max_count and c_count > max_count:
                break

def visualize_gps_data(data_path_csv, dir_path, workdir):
    vis = GPSVis(data_path=data_path_csv,
             map_path='atto_map_crop.png',  # Path to map downloaded from the OSM.
             points=(-2.142586, -59.007617, -2.148917, -58.999867)) # Two coordinates of the map (upper left, lower right)

    vis.create_image(color="cyan", width=5)  # Set the color and the width of the GNSS tracks.
    # os.chdir(dir_path)
    vis.plot_map(output='save', save_as=os.path.join(dir_path, "location.png"))
    # os.chdir(workdir)

def create_data_csv(ext_path):

    ext_files= os.listdir(ext_path)

    df = pd.DataFrame(columns=['Filename', 'Latitude', 'Longitude', 'RelativeAltitude', 'AbsoluteAltitude', 'Drone_Direction', 'Canonical_Drone_Direction', 'Tree_Direction', 'Canonical_Tree_Direction'])
    for f in ext_files:
        if f.endswith(".JPG"):
            file_path = os.path.join(ext_path, f)
            try:
                results, i = cc.get_img_meta(file_path)
                latitude = convert_string_to_float(i.getxmp()['xmpmeta']['RDF']['Description']['GpsLatitude'])
                longitude = convert_string_to_float(i.getxmp()['xmpmeta']['RDF']['Description']['GpsLongitude'])

                rel_heights = convert_string_to_float(i.getxmp()['xmpmeta']['RDF']['Description']['RelativeAltitude'])
                abs_heights = convert_string_to_float(i.getxmp()['xmpmeta']['RDF']['Description']['AbsoluteAltitude'])
                drone_direction = convert_string_to_float(i.getxmp()['xmpmeta']['RDF']['Description']['GimbalYawDegree'])

                canonical_drone_direction = calculate_bearing(float(drone_direction))
                tree_direction = drone_direction + 180
                if tree_direction > 360:
                    tree_direction = tree_direction - 360
                canonical_tree_direction = calculate_bearing(float(tree_direction))

                df = pd.merge(df, pd.DataFrame({
                    'Filename': [f],
                    'Latitude': [latitude],
                    'Longitude': [longitude],
                    'RelativeAltitude': [rel_heights],
                    'AbsoluteAltitude': [abs_heights],
                    'Drone_Direction': [drone_direction],
                    'Canonical_Drone_Direction': [canonical_drone_direction],
                    'Tree_Direction': [tree_direction],
                    'Canonical_Tree_Direction': [canonical_tree_direction]
                }), how='outer', 
                on=['Filename', 'Latitude', 'Longitude', 'RelativeAltitude', 'AbsoluteAltitude', 'Drone_Direction', 'Canonical_Drone_Direction', 'Tree_Direction', 'Canonical_Tree_Direction']
                )

            except Exception as e:
                print("No meta found, skipping...")
                print(e)
                continue


    print(df)
    csv_path = os.path.join(ext_path, "data_v2.csv")
    df.to_csv(csv_path, index=False)
    

def add_tree_location(dst_folder):
    workdir = os.getcwd()
    for root, dirs, files in os.walk(dst_folder):
        for dir_name in dirs:
            if "Tree" in dir_name:
                ext_path = os.path.join(root, dir_name)
                print("Processing ", ext_path)
                create_data_csv(ext_path)
                

if __name__ == "__main__":
    csv_file = "sorted_images.csv"  # csv file with sharpest images
    dst_folder = "data\\sharpest_files"  # destination for the copied files
    folder = r"D:\Mavic-3-Fotos\ATTO"
    # folder = r"C:\Users\faulhamm\Documents\Philipp\Code\cc-data-processing\Tree_data"
    # copy_files_from_csv(csv_file, dst_folder)
    add_tree_location(folder)