import exiftool
import os
import numpy as np
import pandas as pd
from pathlib import Path
import os

def calculate_bearing(degree):
# function from: https://gist.github.com/RobertSudwarts/acf8df23a16afdb5837f
  dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
  ix = int(round(degree / (360. / len(dirs))))
  return dirs[ix % len(dirs)]

base_path = "C:\\Users\\Lopap\\Documents\\Mavic3-Pictures\\Sensor_Test_2601"
compass_files = os.listdir(base_path)


raw_files = [os.path.join(base_path, f) for f in compass_files if f.endswith('DNG')]
lat_list = []
long_list = []

for rf in raw_files:
    with exiftool.ExifToolHelper() as et:
        filename = et.get_metadata(rf)[0]['File:FileName']
        gimbal_yaw_deg = et.get_metadata(rf)[0]['XMP:GimbalYawDegree']
        rel_altitude = et.get_metadata(rf)[0]['XMP:RelativeAltitude']
        abs_altitude = et.get_metadata(rf)[0]['XMP:AbsoluteAltitude']
        long = et.get_metadata(rf)[0]['XMP:GPSLongitude']
        lat = et.get_metadata(rf)[0]['XMP:GPSLatitude']
        
        long_list.append(float(long))
        lat_list.append(float(lat))

        if type(gimbal_yaw_deg) == str:
            degree = float(gimbal_yaw_deg[1:])
        else:
            degree = 360 + gimbal_yaw_deg

        print("-----------------------------------------")
        print("F-Name: ", filename)
        print("Direction [Drone]: {1} ({0} °)".format(degree, calculate_bearing(degree)))
        print("Direction [Tree]: {1} ({0} °)".format(degree-180, calculate_bearing(degree-180)))
        print("Abs. Altitude: ", abs_altitude)
        print("Rel. Altitude: ", rel_altitude)
        print("Long. : ", long)
        print("Lat. :", lat)


data = zip(lat_list, long_list)
frame = pd.DataFrame(data, columns=["Latitude", "Longitude"], index=None)
frame.to_csv("gps_data.csv")