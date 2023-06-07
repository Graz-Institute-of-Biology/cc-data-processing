import os
import time
import shutil
import exifread
from PIL import Image
from PIL.ExifTags import TAGS
import yaml

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

def convert_string_to_float(number_string):
    """cast direction string to float
    from "+FLOAT" or "-FLOAT" to +float or -float

    Args:
        number_string (string): string with float and +/- sign

    Returns:
        float: converted float
    """
    if number_string[0] == "+":
        converted = float(number_string[1:])
    
    elif number_string[0] == "-":
        converted =  -float(number_string[1:])

    return converted

def convert_direction_string(direction_string):
    """ shift direction string to from range (-180, 180) to (0,360)

    Args:
        direction_string (string): string from metadata

    Returns:
        float: converted float value
    """
    converted = convert_string_to_float(direction_string)
    shifted = 180 + converted

    return shifted

def convert_to_tree_direction(direction_drone):
    """calculate direction of the tree surface that faces the drone (opposite direction of drone)

    Args:
        direction_drone (float): drone direction in degrees

    Returns:
        float: tree direction
    """

    if direction_drone < 180:
        new_direction = direction_drone + 180
    elif direction_drone >= 180:
        new_direction = direction_drone - 180

    return new_direction

def get_file_infos(file_path):
    """ returns date (Format: DDMMYY) and 
        direction of gimbal yaw degree (compass direction of the drone) in degrees (0, 360)

    Args:
        file_path (string): path to jpg file

    Returns:
        list: list including [date, gibalYawDegree]
    """
    results = {}
    i = Image.open(file_path)
    info = i._getexif()
    for tag, value in info.items():
        decoded = TAGS.get(tag, tag)
        results[decoded] = value

    date = "".join(results["DateTimeOriginal"].split(" ")[0][2:].split(":")[::-1])
    direction_string = i.getxmp()['xmpmeta']['RDF']['Description']['GimbalYawDegree']
    direction_drone = convert_direction_string(direction_string)
    direction_tree = convert_to_tree_direction(direction_drone)
    rel_altitude_string = i.getxmp()['xmpmeta']['RDF']['Description']['RelativeAltitude']
    rel_altitude = convert_string_to_float(rel_altitude_string)

    return [date, direction_drone, direction_tree, rel_altitude]

def get_tree_height(rel_altitude):
    """return "Ground" if relative altitude is zero (means that drone was used without flying)
    else if relative altitude is greater than 0: return "Main_stem" (drone was flying, capturing main stem)

    Args:
        rel_altitude (float): relative altitude in meters

    Returns:
        int: tree level: 0 means Ground level ; 1 means Main_stem level
    """

    if rel_altitude == 0:
        return "Ground"
    elif rel_altitude > 2:
        return "Main_stem"
    else:
        return "Undecided"
    
def change_height_abbreviation(base_path, old="_M_", new="_C_"):
    """replace height abbreviation: _M_ for mainstem ; _C_ for Canopy ; _G_ for Ground

    Args:
        base_path (string): path of folder to scan and change abbreviations
    """
    for img_name in os.listdir(base_path):
        old_path = os.path.join(base_path, img_name)
        new_path = old_path.replace(old, new)
        print(old_path)
        print(new_path)
        os.rename(old_path, new_path)

def load_path(yaml_file):
    """load path from yaml file

    Args:
        yaml_file (string): path to yaml file

    Returns:
        dict: loaded yaml file
    """
    with open("paths.yaml") as f:
        yaml_file = yaml.safe_load(f)

    return yaml_file["base_path"]

def create_filename_information(base_path):
    """create new file name using DATE, Forest type (TF for TerraFirme or C for Campina)
    direction N,E,S,W ; height abbreviation: G (Ground), M (Mainstem), C (Canopy)
    height information in meters is also used and finally the original DJI naming.

    Example File name: 010223_TF_C_25.2m_E_DJI_0001.JPG [DATE_ForestType_HeightAbbreviation_Height_Direction_DJIname]
    """
    forest_type_code = "TF"
    # tree_height_level = "Main_stem"

    folder_items = os.listdir(base_path)
    
    for item in folder_items:
        if item.endswith(".JPG"):
            path = os.path.join(base_path, item)
            file_infos = get_file_infos(path) # returns: [date, direction_drone, direction_tree, rel_altitude]

            date = file_infos[0]
            height = file_infos[3]
            tree_direction = calculate_bearing(file_infos[2])
            tree_height_level = get_tree_height(height)
    
            stem_level_short = tree_height_level[0]
            new_file_name = "{0}_{1}_{2}_{3}m_{4}_{5}".format(date, forest_type_code, stem_level_short, height, tree_direction, item)
            # new_path = os.path.join(base_path,tree_height_level,directions_dictionary[tree_direction], new_file_name)
            new_path = os.path.join(base_path, new_file_name)
            print("Old path: ", path)
            print("New path: ", new_path)
            
            try:
                os.rename(path, new_path)
            except FileExistsError:
                print("Already processed.")
                print("File {0} skipped".format(item))
                continue

            print("Tree - Degree: {0} | Direction: {1} | Height: {2}".format(file_infos[2], tree_direction, height))
            # print("Tree - RelAlt: {0} | Stem level: {1} ".format(file_infos[3], tree_height_level))

if __name__ == "__main__":


    base_path = load_path("paths.yaml")

    # create_filename_information(base_path) 
    change_height_abbreviation(base_path)


