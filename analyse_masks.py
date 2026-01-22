import os
import cv2
import numpy as np
import pandas as pd
from tqdm import tqdm
import yaml

class MaskAnalysis:
    def __init__(self, yaml_file, output_folder):
        self.yaml_file = yaml_file
        self.output_folder = output_folder
        self.load_yaml()

    def load_yaml(self):
        """load parameters (api key, project id, local save folder) from yaml file
        """
        with open(self.yaml_file) as f:
            yaml_file = yaml.safe_load(f)
        self.mask_folder = yaml_file["mask_folder"]
        self.ontology = yaml_file["ontology"]
        self.class_codes = yaml_file["class_dict"]
        print("Class codes:")
        print(self.class_codes)
        self.ending = yaml_file["ending"]
        # self.class_dict = yaml_file["class_dict"]

        print("yaml file loaded:")
        print("Ontology: ", self.ontology)
        print("class codes: ", self.class_codes)

    def read_full_data_df(self):
        self.full_data_df = pd.read_excel("Data_full.xlsx")
        print("Full data dataframe loaded:")
        print(self.full_data_df)

    def create_class_df(self):
        class_list = []
        for key, value in self.class_codes.items():
            class_list.append({"class_name": key, "class_code": value})
        self.class_df = pd.DataFrame(class_list)

        self.analysis_dataframe = pd.DataFrame(columns=["image", "height", "orientation", "tree_number", "tree_species"] + list(self.class_codes.keys()))

    def analyse_image_values(self):

        mask_list = self.full_data_df['Filename'].apply(lambda x: x.replace('.jpg', '_mask.png')).tolist()
        class_names = list(self.full_data_df.columns[6:])
        mask_not_found = 0

        for mask_idx, mask_file in enumerate(mask_list):
            mask_path = os.path.join(self.output_folder, mask_file)
            mask = cv2.imread(mask_path, cv2.IMREAD_UNCHANGED)
            if mask is not None:
                class_dist = np.zeros(len(class_names))
                tree_surface_pixels = np.sum(mask > 0)


                for class_idx, class_name in enumerate(class_names):
                    class_name = class_name.lower()
                    value = self.class_codes[class_name]
                    class_pixels = np.sum(mask == value)
                    class_dist[class_idx] = class_pixels / tree_surface_pixels
                
                results_dict = dict(zip(class_names, class_dist))
                self.full_data_df.loc[self.full_data_df.index[mask_idx], list(results_dict.keys())] = list(results_dict.values())


            else:
                print("Mask not found: ", mask_path)
                mask_not_found += 1

        print("Done. Masks not found: ", mask_not_found)
        self.full_data_df.to_excel("full_data_mask_analysis.xlsx", index=False)

if __name__ == "__main__":

    output_folder = 'C:\\Users\\faulhamm\\Documents\\Philipp\\Code\\cc-machine-learning\\results\\03-cc-graz\\lara_final_analysis'
    os.makedirs(output_folder, exist_ok=True)

    yaml_file = 'C:\\Users\\faulhamm\\Documents\\Philipp\\Code\\cc-data-processing\\labelbox_graz_sep.yaml'

    mask_analysis = MaskAnalysis(yaml_file, output_folder)
    mask_analysis.read_full_data_df()
    mask_analysis.create_class_df()
    mask_analysis.analyse_image_values()
