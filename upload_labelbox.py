import labelbox as lb
import labelbox.data.annotation_types as lb_types
from export_labelbox import labelbox_exporter
from PIL import Image
from tqdm import tqdm
import time
import os
import numpy as np
import yaml
import pandas as pd
import uuid


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

def perform_upload(client, project, img_name, mask, class_names):
    # categorical mask values!!!
    labels = []
    annotations = []

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
        lb_types.Label(data={"global_key" : img_name},
                    annotations=annotations))
    

    # Upload MAL label for this data row in project
    upload_job = lb.MALPredictionImport.create_from_objects(
        client = client, 
        project_id = project.uid, 
        name="mal_job"+img_name+str(uuid.uuid4()), 
        predictions=labels
    )

    print(upload_job)
    upload_job.wait_till_done()

    print("Errors: ", upload_job.errors)
    # try:
    #     print(upload_job.errors)
    # except ValueError:
    #     print("Upload successful?")

def upload_masks(yaml_file, dataset_code="None", remove_uploaded_mask=False):
    exporter = labelbox_exporter(yaml_file)
    exporter.get_export_json()
    exporter.get_to_label_list() # get list of labelbox data rows with status "TO_LABEL"

    to_label_list = exporter.to_label_list
    exif_rot_dict = exporter.exif_rot_dict
    client = exporter.lb_client
    project = exporter.lb_project
    mask_folder = exporter.mask_folder
    ending = exporter.ending

    if dataset_code == "None":
        dataset_code = ""

    class_names = list(exporter.class_codes.keys())

    # mask_file = np.array(Image.open(mask_path))
    mask_files = [os.path.join(mask_folder, x) for x in os.listdir(mask_folder) if x.endswith("mask.png")]
    print(mask_folder)
    upload_count = 1
    for mask_file in mask_files:
        img_name = os.path.basename(mask_file).split("_mask")[0] + dataset_code + ending
        if img_name in to_label_list:
            print("Uploading mask {0} of {1}".format(upload_count, len(to_label_list)))
            mask = np.array(Image.open(mask_file))
            print("Mask size: ", mask.shape)
            if exif_rot_dict[img_name] == 8:
                mask = np.rot90(mask, k=3)
                print("Rotated clockwise: ", exif_rot_dict[img_name])
            elif exif_rot_dict[img_name] == 6:
                mask = np.rot90(mask)
                print("Rotated counter clockwise: ", exif_rot_dict[img_name])
            elif exif_rot_dict[img_name] == 3:
                mask = np.rot90(mask, k=2)
                print("Rotated 180 degrees: ", exif_rot_dict[img_name])
            try:
                perform_upload(client, project, img_name, mask, class_names)
                if remove_uploaded_mask:
                    os.remove(mask_file)
                print("Uploaded mask {0} of {1}".format(upload_count, len(to_label_list)))
                print("-----------------------------------------------------")
            except Exception as err:
                print(f'Error while uploading mask -  Error: {err}')
                continue
            upload_count += 1

def assign_global_keys(yaml_file, dataset_code="None"):
    """ create labelbox object, get export json and assign global keys to images with status "TO_LABEL"
    """

    if dataset_code == "None":
        dataset_code = ""
    exporter = labelbox_exporter(yaml_file=yaml_file)
    exporter.get_export_json()
    exporter.assign_global_keys(dataset_code=dataset_code) # assign global keys using image names NO CHECK IF UNIQUE NAMES ARE USED

def delete_imported_labels(yaml_file):
    """ delete all imported labels from project
    """
    exporter = labelbox_exporter(yaml_file)
    exporter.get_export_json()
    exporter.get_to_label_list()

    project_id = exporter.lb_project.uid
    client = exporter.lb_client

    query = """
    query GetBulkImportRequests($projectId: ID!) {
        bulkImportRequests(where: {projectId: $projectId}) {
            id
            name
            state
            createdAt
            inputFileUrl
            errorFileUrl
        }
    }
    """
    
    print(f"🔍 Searching for MAL imports in project {project_id}...")
    
    try:
        # Execute the query
        result = client.execute(query, {"projectId": project_id})
        
        if 'bulkImportRequests' not in result:
            print("❌ Error: Could not retrieve bulk import requests")
            print("Response:", result)
            return
        
        imports = result['bulkImportRequests']

        if not imports:
            print("✅ No MAL imports found in this project")
            return
        
        print(f"📋 Found {len(imports)} MAL import(s):")
        for i, imp in enumerate(imports):
            print(f"  {i+1}. ID: {imp['id']}")
            print(f"     Name: {imp['name']}")
            print(f"     State: {imp['state']}")
            print(f"     Created: {imp['createdAt']}")
            print()
        
        # Step 2: Delete each import
        delete_mutation = """
        mutation DeleteBulkImportRequest($importId: ID!) {
            deleteBulkImportRequest(where: {id: $importId}) {
                id
                name
            }
        }
        """
        
        deleted_count = 0
        failed_count = 0
        
        for imp in imports:
            import_id = imp['id']
            import_name = imp['name']
            
            print(f"🗑️  Deleting import: {import_name} ({import_id})")
            
            try:
                delete_result = client.execute(delete_mutation, {"importId": import_id})
                
                if 'deleteBulkImportRequest' in delete_result and delete_result['deleteBulkImportRequest']:
                    print(f"   ✅ Successfully deleted: {import_name}")
                    deleted_count += 1
                else:
                    print(f"   ❌ Failed to delete: {import_name}")
                    print(f"   Response: {delete_result}")
                    failed_count += 1
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ Error deleting {import_name}: {str(e)}")
                failed_count += 1
        
        # Summary
        print(f"\n📊 Deletion Summary:")
        print(f"   ✅ Successfully deleted: {deleted_count}")
        print(f"   ❌ Failed to delete: {failed_count}")
        print(f"   📋 Total processed: {len(imports)}")
        
        if deleted_count > 0:
            print(f"\n⚠️  Note: Deletion is permanent and cannot be undone!")
            print(f"   You may need to refresh the Labelbox UI to see changes.")
        
    except Exception as e:
        print(f"❌ Error executing GraphQL query: {str(e)}")
        print("Make sure your API key has the necessary permissions.")

def clear_global_keys():
    keys_to_clear = ["1.2.JPG", "1.5.JPG"]
    dataset_id = "cm84n1vwo004d0746gdqu5t0u"
    exporter = labelbox_exporter(yaml_file)
    exporter.get_export_json()
    exporter.clear_global_keys(clear_all=True)



if __name__ == "__main__":

    # ATTO
    # yaml_file = "labelbox.yaml"
    # yaml_file = "labelbox_tf_increase.yaml"

    # GROßGLOCKNER
    # yaml_file = "labelbox_gg.yaml"
    # yaml_file = "labelbox_gg_june24.yaml"
    # yaml_file = "labelbox_gg_july24.yaml"
    # yaml_file = "labelbox_gg_august24.yaml"
    # yaml_file = "labelbox_gg_september24.yaml"

    # yaml_file = "labelbox_gg_june25.yaml"
    # yaml_file = "labelbox_gg_july25.yaml"
    # yaml_file = "labelbox_gg_july3025.yaml"
    # yaml_file = "labelbox_gg_august2625.yaml"
    # yaml_file = "labelbox_gg_october1225.yaml"

    yaml_file = "labelbox_cc_october25.yaml" # cc = climate chamber

    # GRAZ
    # yaml_file = "labelbox_graz.yaml"
    # yaml_file = "labelbox_graz_june.yaml"
    # yaml_file = "labelbox_graz_sep.yaml"

    # delete_previous_labels = True
    if "gg_" in yaml_file:
        dataset_code = "_" + yaml_file.split("_")[2].split(".")[0]
    else:
        dataset_code = ""


    # GLOBAL KEY STUFF
    print(dataset_code)

    # delete_imported_labels(yaml_file)

    # clear_global_keys()
    # assign_global_keys(yaml_file, dataset_code=dataset_code) # assign global keys using image names NO CHECK IF UNIQUE NAMES ARE USED
    
    upload_masks(yaml_file, dataset_code=dataset_code, remove_uploaded_mask=True) # upload masks to data row with status "TO_LABEL"
