import labelbox as lb
import labelbox.data.annotation_types as lb_types
from export_labelbox import labelbox_exporter
from PIL import Image

import os
import numpy as np
import yaml
import pandas as pd
import uuid

CLASS_DICT  =    {	    "Background" : 0,
                        "Liverwort" : 1,
                        "Moss" : 2,
                        "CyanosLiverwort" : 3,
                        "CyanosMoss" : 4,
                        "Lichen" : 5,
                        "BarkDominated" : 6,
                        "CyanosBark" : 7,
                        "Other" : 8,
                    }

def upload_images(client, data_path):

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

def perform_upload(client, project, img_name, mask):
    # categorical mask values!!!
    labels = []
    annotations = []
    class_names = list(CLASS_DICT.keys())
    class_values = np.unique(mask)
    # leave out background (label: 0)
    for class_value in class_values[1:]:
        color = (class_value, class_value, class_value)

        
        mask_data = lb_types.MaskData.from_2D_arr(arr=mask)
        mask_annotation = lb_types.ObjectAnnotation(
            name = class_names[class_value], # must match your ontology feature"s name
            value=lb_types.Mask(mask=mask_data, color=color),
            )
        annotations.append(mask_annotation)

    labels.append(
        lb_types.Label(data=lb_types.ImageData(global_key=img_name),
                    annotations=annotations))
    

    # Upload MAL label for this data row in project
    upload_job = lb.MALPredictionImport.create_from_objects(
        client = client, 
        project_id = project.uid, 
        name="mal_job"+img_name+str(uuid.uuid4()), 
        predictions=labels
    )

    if len(upload_job.errors) > 0:
        print(upload_job.errors)
    else:
        print("Upload successful")

def upload_masks(client, project, to_label_list, mask_folder):

    # mask_file = np.array(Image.open(mask_path))
    mask_files = [os.path.join(mask_folder, x) for x in os.listdir(mask_folder) if x.endswith(".png")]
    upload_count = 1
    for mask_file in mask_files:
        img_name = os.path.basename(mask_file).split(".png")[0] + ".JPG"
        if img_name in to_label_list:
            print("Uploading mask {0} of {1}".format(upload_count, len(to_label_list)))
            mask = np.array(Image.open(mask_file))
            print(img_name)
            print(np.unique(mask))

            perform_upload(client, project, img_name, mask)
            print("-----------------------------------------------------")
            upload_count += 1


if __name__ == "__main__":

    exporter = labelbox_exporter()
    exporter.get_export_json()
    exporter.assign_global_keys() # assign global keys using image names NO CHECK IF UNIQUE NAMES ARE USED
    exporter.get_to_label_list() # get list of labelbox data rows with status "TO_LABEL"

    to_label_list = exporter.to_label_list
    client = exporter.lb_client
    project = exporter.lb_project
    mask_folder = exporter.mask_folder

    upload_masks(client, project, to_label_list, mask_folder) # upload masks to data row with status "TO_LABEL"