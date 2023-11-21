import labelbox
from labelbox.schema.bulk_import_request import BulkImportRequest
import yaml
import requests
import os
from matplotlib import pyplot as plt
import cv2
import numpy as np
from PIL import Image
import os
import shutil

# workflow names: DONE, IN_REVIEW, IN_REWORK, TO_LABEL

class labelbox_exporter:

	def __init__(self, yaml_file="labelbox.yaml") -> None:

		self.yaml_file = yaml_file
		self.load_yaml()

		self.headers = {'Authorization': self.lb_api_key}
		self.lb_client = labelbox.Client(api_key = self.lb_api_key)
		self.lb_project = self.lb_client.get_project(self.lb_project_id)
		self.exported_images = []

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
		self.mask_folder = yaml_file["mask_folder"]



	def get_export_json(self):
		"""get export json from specific project
		"""
		export_task = self.lb_project.export_v2(params=self.export_params)
		export_task.wait_till_done()

		if export_task.errors:
			print(export_task.errors)

		self.export_json = export_task.result

		# print(self.export_json)


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
				# print(img['projects'][self.lb_project_id]['project_details']['workflow_history'][0]['action'])
				# last_action = img['projects'][self.lb_project_id]['project_details']['workflow_history'][0]['action']
				workflow_status = img['projects'][self.lb_project_id]['project_details']['workflow_status']
			else:
				continue

			# check if image workflow status is DONE
			if workflow_status == 'DONE':
				objects = img['projects'][self.lb_project_id]['labels'][0]['annotations']['objects']
				original_name = img['data_row']['external_id']
				self.exported_images.append(original_name)
				if original_name.replace(".JPG",".png") in self.saved_masks:
					print("File: {0} already processed".format(original_name))
					print("continueing...")
					continue
				else:
					img_count += 1
					print("Preparing new mask:", original_name)
					self.download_and_process_mask(original_name, objects, combine_masks)


		if img_count == 0:
			print("No new files found")
		else:
			print("{0} new mask(s) added".format(img_count))

	def get_unique_values(self, mask_files):
		
		values = [np.unique(np.array(Image.open(mask))) for mask in mask_files]
		flattened = [val for sublist in values for val in sublist]
	
		return np.unique(np.array(flattened))

	def combine_and_save_mask(self, base_file, mask_files):

		im_frame = Image.open(mask_files[0])
		np_frame = np.array(im_frame)
		combined_mask = np.zeros(np_frame.shape)

		for mask in mask_files:
			im_frame = Image.open(mask)
			np_frame = np.array(im_frame)
			label_positions = np_frame > 0
			combined_mask[label_positions] = np_frame[label_positions]
			# combined_mask += np_frame

		im = Image.fromarray(combined_mask.astype(np.uint8))
		im.save(os.path.join(self.mask_save_path, base_file.replace(".JPG",".png")))



	
	def delete_imported_labels(self):
		# imports = self.lb_client.get_bulk_import_requests()
		for file_name in self.to_label_list:
			data_row = self.lb_client.get_data_row_by_global_key(file_name)
			print("DELETE: ", data_row.external_id)
			data_row.delete()

	def get_to_label_list(self):
		to_label_list = []
		for img in self.export_json:
			workflow_status = img['projects'][self.lb_project_id]['project_details']['workflow_status']
			if workflow_status == "TO_LABEL":
				to_label_list.append(img['data_row']['global_key'])

		self.to_label_list = to_label_list

	def assign_global_keys(self):
		global_key_data_row_inputs = []

		# print(self.export_json)
		for img in self.export_json:
			workflow_status = img['projects'][self.lb_project_id]['project_details']['workflow_status']
			if not workflow_status == "DONE":
				print(img['data_row']['external_id'])
				global_key_data_row_inputs.append({"data_row_id": img['data_row']['id'], "global_key": img['data_row']['external_id']})

		# print(global_key_data_row_inputs)
		self.lb_client.assign_global_keys_to_data_rows(global_key_data_row_inputs)

if __name__ == "__main__":

	exporter = labelbox_exporter()
	exporter.get_export_json()
	# exporter.get_to_label_list()
	# exporter.delete_imported_labels()
	# exporter.assign_global_keys()

	# exporter.get_masks()
	# exporter.copy_related_images()
