import labelbox
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

	def __init__(self, yaml_file, foreground_only=False) -> None:

		self.yaml_file = yaml_file
		self.load_yaml()

		self.headers = {'Authorization': self.lb_api_key}
		self.lb_client = labelbox.Client(api_key = self.lb_api_key)
		self.lb_project = self.lb_client.get_project(self.lb_project_id)
		print(self.lb_project.name)
		self.exported_images = []
		self.foreground_only = foreground_only

		self.export_params = {
							"data_row_details": True,
							"metadata": True,
							"attachments": True,
							"project_details": True,
							"performance_details": True,
							"label_details": True,
							"interpolated_frames": True
							}

		# if self.ontology == "atto":
		# 	self.class_codes = {	"liverwort" : 1,
		# 							"moss" : 2,
		# 							"cyanosliverwort" : 3,
		# 							"cyanosmoss" : 4,
		# 							"lichen" : 5,
		# 							"barkdominated" : 6,
		# 							"cyanosbark" : 7,
		# 							"other" : 8,}
			
		# elif self.ontology == "gg":
		# 	self.class_codes = {	
		# 							"cyano - dominated" : 1,
		# 							"lichen" : 2,
		# 							"moss" : 3,
		# 							"vascular plants" : 4,
		# 							"rock" : 5,
		# 							"other" : 6,
		# 							"fungi" : 7,
		# 							"markers" : 8,
		# 							"snow" : 9,}
			
		# elif self.ontology == "graz":
		# 	self.class_codes = {
		# 							"background" : 0,
		# 							"bryophyte" : 1,
		# 							"lichen" : 2,
		# 							"barkdominated" : 3,
		# 							"other" : 4,
		# 	}
		
	def load_yaml(self):
		"""load parameters (api key, project id, local save folder) from yaml file
		"""
		with open(self.yaml_file) as f:
			yaml_file = yaml.safe_load(f)

		self.save_folder = yaml_file["save_folder"]
		self.combined_mask_path = os.path.join(self.save_folder, "combined_masks")
		self.labelbox_mask_path = yaml_file["labelbox_mask_path"]
		self.saved_masks = os.listdir(self.combined_mask_path)
		self.lb_api_key = yaml_file["api_key"]
		self.lb_project_id = yaml_file["project_id"]
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


	def get_all_global_keys(self):

		global_keys = []
		for data_row in self.export_json:
			global_keys.append(data_row['data_row']['global_key'])

		return global_keys

	def clear_global_keys(self, global_keys_to_clear=None, clear_all=False):
		if clear_all:
			print("Getting all global keys...")
			global_keys_to_clear = self.get_all_global_keys()
			print("Global keys to clear:")
			print(global_keys_to_clear)

		if not global_keys_to_clear == None:
			print("Clearing global keys...")
			print(global_keys_to_clear)

		job_result = self.lb_client.clear_global_keys(global_keys_to_clear)
		print(job_result)

	def get_export_json(self):
		"""get export json from specific project
		"""
		export_task = self.lb_project.export_v2(params=self.export_params)
		print("Getting json...")
		export_task.wait_till_done()

		if export_task.errors:
			print(export_task.errors)

		self.export_json = export_task.result

		print("Done")
		# print(self.export_json)


	def download_and_process_mask(self, original_name, objects, combine_masks, exif_rot):
		mask_files = []
		# iterate over all class masks (lichen, moss, etc)
		object_count = 0
		for object in objects:
			label = object['name'].lower()
			try:
				archived = object['archived']
			except KeyError:
				archived = False

			if archived:
				continue

			url = object['mask']['url']

			if original_name.endswith(".jpg"):
				original_name = original_name.replace(".jpg", ".JPG")

			file_name = original_name.replace(".JPG", "") + "_" + label +"_{0}".format(object_count) + "_mask.png"

			while True:
				if os.path.exists(os.path.join(self.labelbox_mask_path, file_name)):
					object_count += 1
					file_name = original_name.replace(".JPG", "") + "_" + label +"_{0}".format(object_count) + "_mask.png"
				else:
					# file_name = original_name.replace(".JPG", "") + "_" + label +"_{0}".format(object_count) + "_mask.png"
					object_count = 0
					break
				
			file_path = os.path.join(self.labelbox_mask_path, file_name)
			response = requests.get(url, headers=self.headers, stream=True).raw
			image = np.asarray(bytearray(response.read()), dtype="uint8")
			image = cv2.imdecode(image, cv2.IMREAD_GRAYSCALE)
			print("mask:", url)
			mask = np.where(image == 255)
			image[mask] = self.class_codes[label]
			cv2.imwrite(file_path, image)

			mask_files.append(file_path)

		if combine_masks:
			base_file = original_name
			self.combine_and_save_mask(base_file, mask_files, exif_rot)

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
				exif_rot = int(img['media_attributes']['exif_rotation'])
				original_name = img['data_row']['external_id']
				self.exported_images.append(original_name)
				if original_name.replace(".JPG",".png") in self.saved_masks:
					print("File: {0} already processed".format(original_name))
					print("continueing...")
					continue
				else:
					img_count += 1
					print("Preparing new mask:", original_name)
					self.download_and_process_mask(original_name, objects, combine_masks, exif_rot)


		if img_count == 0:
			print("No new files found")
		else:
			print("{0} new mask(s) added".format(img_count))

	def get_unique_values(self, mask_files):
		
		values = [np.unique(np.array(Image.open(mask))) for mask in mask_files]
		flattened = [val for sublist in values for val in sublist]
	
		return np.unique(np.array(flattened))
	
	def check_rotation(self, mask, base_file, exif_rot):
		img_name = base_file.replace(".JPG","")
		print("Checking rotation for: ", img_name)
		print("Exif rotation: ", exif_rot)

		if exif_rot == 8:
			mask = np.rot90(mask)
			print("Rotated counter clockwise")
		elif exif_rot == 6:
			mask = np.rot90(mask, k=3)
			print("Rotated clockwise")
		elif exif_rot == 3:
			# mask = np.rot90(mask, k=2)
			print("WARNING: EXIF_ROT ", exif_rot)
			print("WHY ???? 180 Degrees? MAKES NO SENSE!!")
			print("CHECK: ", img_name)

		return mask

	def combine_and_save_mask(self, base_file, mask_files, exif_rot):

		im_frame = Image.open(mask_files[0])
		np_frame = np.array(im_frame)
		combined_mask = np.zeros(np_frame.shape)

		for mask in mask_files:
			im_frame = Image.open(mask)
			np_frame = np.array(im_frame)
			label_positions = np_frame > 0
			combined_mask[label_positions] = np_frame[label_positions]
			# combined_mask += np_frame
		if self.foreground_only:
			combined_mask = np.where(combined_mask > 0, 1, 0)

		if exif_rot != 1:
			print("Checking rotation: {0} || {1}".format(exif_rot, base_file))
			combined_mask = self.check_rotation(combined_mask, base_file, exif_rot)
		im = Image.fromarray(combined_mask.astype(np.uint8))
		im.save(os.path.join(self.combined_mask_path, base_file.replace(".JPG",".png")))


	def copy_related_images(self, copy_imgs = "masks"):

		if copy_imgs == "masks":
			related_images = self.exported_images
			dst_folder = "C:\\Users\\faulhamm\\Documents\\Philipp\\training\\imgs"

		elif copy_imgs == "to_label":
			related_images = self.to_label_list
			dst_folder = "C:\\Users\\faulhamm\\Documents\\Philipp\\Code\\cc-machine-learning\\test"

		self.data_path = "C:\\Users\\faulhamm\\OneDrive - Universität Graz\\Dokumente\\Philipp\\Data"
		for file in related_images:
			for dirpath, dirnames, filenames in os.walk(self.data_path):
				for filename in [f for f in filenames if f.endswith(file)]:
					src = os.path.join(dirpath, filename)
					print("COPY: ", src)
					shutil.copy2(src, dst_folder)
	
	def delete_imported_labels(self):
		# imports = self.lb_client.get_bulk_import_requests()
		for file_name in self.to_label_list:
			data_row = self.lb_client.get_data_row_by_global_key(file_name)
			print("DELETE: ", data_row.external_id)
			data_row.delete()

	def get_to_label_list(self, print_list=False):
		to_label_list = []
		exif_rot_dict = {}
		for img in self.export_json:
			workflow_status = img['projects'][self.lb_project_id]['project_details']['workflow_status']
			if workflow_status == "TO_LABEL":
				try:
					to_label_list.append(img['data_row']['global_key'])
					exif_rot_dict[img['data_row']['global_key']] = int(img['media_attributes']['exif_rotation'])
				except KeyError:
					print("No global key:")
					print(img['data_row']['external_id'])

		if print_list:
			print(to_label_list)

		self.to_label_list = to_label_list
		self.exif_rot_dict = exif_rot_dict
		print(self.exif_rot_dict)

	def assign_global_keys(self, dataset_code):
		global_key_data_row_inputs = []
		# upload_list = ["3.4.JPG", "3.6.JPG"]
		# print(self.export_json)

		for img in self.export_json:
			workflow_status = img['projects'][self.lb_project_id]['project_details']['workflow_status']
			if workflow_status == "TO_LABEL":
				print(img['data_row']['external_id'])
				name, extension = os.path.splitext(img['data_row']['external_id'])
				global_key = name + dataset_code + extension
				global_key_data_row_inputs.append({"data_row_id": img['data_row']['id'], "global_key": global_key})

		# print(global_key_data_row_inputs)
		self.lb_client.assign_global_keys_to_data_rows(global_key_data_row_inputs)
		

def download_completed_image_masks(exporter):
	"""download all completed image masks from labelbox
	and copy original images to training folder
	"""
	exporter.get_export_json()
	exporter.get_masks()
	# exporter.copy_related_images(copy_imgs="masks")


def assign_keys(exporter):
	"""assign global keys to images in step "TO_LABEL" in labelbox
	"""
	exporter.get_export_json()
	exporter.get_to_label_list() # get images with status "TO_LABEL"
	exporter.assign_global_keys() # assign keys to images with status "TO_LABEL"

if __name__ == "__main__":
	# ATTO
	# yaml_file = "labelbox.yaml"

	# GROßGLOCKNER
	# yaml_file = "labelbox_gg.yaml"
	# yaml_file = "labelbox_gg_june24.yaml"
	# yaml_file = "labelbox_gg_july24.yaml"
	# yaml_file = "labelbox_gg_august24.yaml"
	# yaml_file = "labelbox_gg_september24.yaml"

	# GRAZ
	# yaml_file = "labelbox_graz.yaml"
	# yaml_file = "labelbox_graz_june.yaml"
    yaml_file = "labelbox_graz_sep.yaml"

    exporter = labelbox_exporter(yaml_file=yaml_file, foreground_only=False)

    download_completed_image_masks(exporter=exporter)

	# exporter.get_export_json()
	# exporter.assign_global_keys()
	# exporter.get_to_label_list(print_list=True)
	# exporter.copy_related_images(copy_imgs="to_label")
	# exporter.delete_imported_labels()

	# exporter.get_masks()
	# exporter.copy_related_images(copy_imgs="masks")
