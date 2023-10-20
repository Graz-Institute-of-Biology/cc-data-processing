import os
import time
import shutil
import exifread
from PIL import Image
from PIL.ExifTags import TAGS
import yaml

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
    rel_altitude_string = i.getxmp()['xmpmeta']['RDF']['Description']['RelativeAltitude']

    return [date, direction_string, rel_altitude_string]


file_name = "C:\\Users\\faulhamm\\OneDrive - Universität Graz\\Dokumente\\Philipp\\Data\\sample_poster_images\\270223_TF_C_W_DJI_0389.JPG"
print(get_file_infos(file_name))