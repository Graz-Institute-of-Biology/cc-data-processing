import labelbox
import yaml
import requests
import os
from matplotlib import pyplot as plt
import cv2
import numpy as np
from PIL import Image

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
		self.mask_save_path = os.path.join(self.save_folder, "combined_masks")
		self.partial_mask_save_path = os.path.join(self.save_folder, "partial_masks")
		self.saved_masks = os.listdir(self.mask_save_path)
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


	def download_and_process_mask(self, original_name, objects, combine_masks):
		mask_files = []
		# iterate over all class masks (lichen, moss, etc)
		for object in objects:
			label = object['name'].lower()
			url = object['mask']['url']

			file_name = original_name.replace(".JPG", "") + "_" + label + ".png"
			file_path = os.path.join(self.partial_mask_save_path, file_name)
			response = requests.get(url, headers=self.headers, stream=True).raw
			image = np.asarray(bytearray(response.read()), dtype="uint8")
			image = cv2.imdecode(image, cv2.IMREAD_GRAYSCALE)
			mask = np.where(image == 255)
			image[mask] = self.class_codes[label]
			cv2.imwrite(file_path, image)

			mask_files.append(file_path)

		if combine_masks:
			base_file = original_name
			self.combine_and_save_mask(base_file, mask_files)

	def get_masks(self, combine_masks=True):
		"""iterate over image infos from labelbox (stored in self.export_json)
		get all class mask URLs for all APPROVED images
		and then download and save masks as png to self.save_folder and combine
		single mask files into one mask png
		"""

		img_count = 0
		for img in self.export_json:

			if len(img['projects'][self.lb_project_id]['project_details']['workflow_history']) > 0:
				last_action = img['projects'][self.lb_project_id]['project_details']['workflow_history'][0]['action']
			else:
				continue

			# check if image is APPROVED
			if last_action == 'Approve':
				objects = img['projects'][self.lb_project_id]['labels'][0]['annotations']['objects']
				original_name = img['data_row']['external_id']
				if original_name.replace(".JPG","_mask.png") in self.saved_masks:
					# print("File: {0} already processed".format(original_name))
					# print("continueing...")
					continue
				else:
					img_count += 1
					print("Preparing new mask:", original_name)
					self.download_and_process_mask(original_name, objects, combine_masks)


		if img_count == 0:
			print("No new files found")
		else:
			print("{0} new mask(s) added".format(img_count))


	def combine_and_save_mask(self, base_file, mask_files):

		im_frame = Image.open(mask_files[0])
		np_frame = np.array(im_frame)
		combined_mask = np.zeros(np_frame.shape)

		for mask in mask_files:
			im_frame = Image.open(mask)
			np_frame = np.array(im_frame)
			combined_mask += np_frame

		im = Image.fromarray(combined_mask.astype(np.uint8))
		im.save(os.path.join(self.mask_save_path, base_file.replace(".JPG","_mask.png")))





if __name__ == "__main__":

	exporter = labelbox_exporter()
	exporter.get_export_json()
	exporter.get_masks()
