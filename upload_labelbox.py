import labelbox as lb
import os
import numpy as np
import yaml
import pandas as pd

with open("paths.yaml") as f:
    yaml_file = yaml.safe_load(f)

data_path = yaml_file["data_path"]

with open("labelbox.yaml") as f:
    yaml_file = yaml.safe_load(f)

api_key = yaml_file["api_key"]
client = lb.Client(api_key=api_key)

new_dataset = client.create_dataset(name = "ATTO-TerraFirme-Ground-North")

# all_files = np.array_split([os.path.join(data_path, x) for x in os.listdir(data_path)], 50)
all_files = [os.path.join(data_path, x) for x in os.listdir(data_path)]

file_frame = pd.DataFrame(columns=["filename", "uploaded"])

for n in range(len(all_files)):
  print("Uploading file {0} ...".format(n))
  print(all_files[n])

  try:
      task = new_dataset.create_data_rows([all_files[n]])
      task.wait_till_done()
      data = pd.DataFrame([{"filename" : all_files[n], "uploaded" : True}])
      print("Upload of file {0} done".format(n))
      print("-----------------------------------------------------")

  except Exception as err:
      print(f'Error while creating labelbox dataset -  Error: {err}')
      print("-----------------------------------------------------")

      data = pd.DataFrame([{"filename" : all_files[n], "uploaded" : False}])
    
  finally:
     file_frame = pd.concat([file_frame, data])


file_frame.to_csv("firme_file_upload.csv")