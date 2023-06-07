import labelbox
import yaml
import requests
import os
from matplotlib import pyplot as plt
import cv2
import numpy as np


class labelbox_exporter:

	def __init__(self, yaml_file="labelbox.yaml") -> None:

		self.yaml_file = yaml_file
		self.load_yaml()

		self.headers = {'Authorization': self.lb_api_key}
		self.lb_client = labelbox.Client(api_key = self.lb_api_key)
		self.lb_project = self.lb_client.get_project(self.lb_project_id)

		self.export_params = {
							"data_row_details": True,
							"metadata": True,
							"attachments": True,
							"project_details": True,
							"performance_details": True,
							"label_details": True,
							"interpolated_frames": True
							}

		self.class_codes = {	"liverwort" : 1,
								"moss" : 2,
								"cyanosliverwort" : 3,
								"cyanosmoss" : 4,
								"lichen" : 5,
								"barkdominated" : 6,
								"cyanosbark" : 7,
								"other" : 8,}
		
		
	def load_yaml(self):
		"""load parameters (api key, project id, local save folder) from yaml file
		"""
		with open(self.yaml_file) as f:
			yaml_file = yaml.safe_load(f)

		self.save_folder = yaml_file["save_folder"]
		self.lb_api_key = yaml_file["api_key"]
		self.lb_project_id = yaml_file["project_id"]


	def get_export_json(self):
		"""get export json from specific project
		"""
		export_task = self.lb_project.export_v2(params=self.export_params)
		export_task.wait_till_done()

		if export_task.errors:
			print(export_task.errors)

		self.export_json = export_task.result


	def download_masks(self):
		"""iterate over images infos from labelbox (stored in self.export_json)
		get all class mask URLs for all APPROVED images
		and then download and save masks as png to self.save_folder
		"""

		for img in self.export_json:
			last_action = img['projects'][self.lb_project_id]['project_details']['workflow_history'][0]['action']

			# check if image is APPROVED
			if last_action == 'Approve':
				objects = img['projects'][self.lb_project_id]['labels'][0]['annotations']['objects']

				# iterate over all class masks (lichen, moss, etc)
				for object in objects:
					original_name = img['data_row']['external_id']
					label = object['name'].lower()
					url = object['mask']['url']

					file_name = original_name.replace(".JPG", "") + "_" + label + ".png"
					file_path = os.path.join(self.save_folder, file_name)
					print(file_name)
					response = requests.get(url, headers=self.headers, stream=True).raw
					image = np.asarray(bytearray(response.read()), dtype="uint8")
					image = cv2.imdecode(image, cv2.IMREAD_GRAYSCALE)
					mask = np.where(image == 255)
					image[mask] = self.class_codes[label]
					cv2.imwrite(file_path, image)







if __name__ == "__main__":

	exporter = labelbox_exporter()
	exporter.get_export_json()
	exporter.download_masks()