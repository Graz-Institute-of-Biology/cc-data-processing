import os
import yaml
from matplotlib import pyplot as plt
import cv2
from skimage import measure
from PIL import Image
import numpy as np
import matplotlib.patches as patches
import cmasher as cmr
import random
from tqdm import tqdm


def get_props(mask_data):
    mask_data_ = mask_data.copy()
    mask_data_[mask_data > 0] = 1
    return measure.regionprops(mask_data_)

def remove_background(img, mask):
    mask_ = mask.copy()
    mask_[mask_ > 0] = 1
    mask_ = np.expand_dims(mask_, axis=2)
    img = img*mask_

    return img

def create_sub_img(img_data, mask_data, file_name, ending, image_month_extension, side=1024, preview=False, remove_original_background=True):

    # find largest connected mask area for cropping
    props = get_props(mask_data)
    bbox = props[0].bbox
    # print(img_data.shape)
    # print(bbox)

    bbox_new = np.array(bbox)
    shift = int(side/4)
    if bbox[1] - shift > 0:
        bbox_new[1] = int(bbox[1] - shift)
    else:
        bbox_new[1] = 0
    
    if bbox[0] - shift > 0:
        bbox_new[0] = int(bbox[0] - shift)
    else:
        bbox_new[0] = 0

    bbox = tuple(bbox_new)

    bbox_height = bbox[2]-bbox[0] + shift
    if bbox_height > img_data.shape[0]:
        bbox_height = img_data.shape[0]
    y_steps = np.arange(round(bbox_height/side))
    n_y_steps = len(y_steps)
    y_step_len = bbox_height/n_y_steps

    bbox_width = bbox[3]-bbox[1] + shift
    if bbox_width > img_data.shape[1]:
        bbox_width = img_data.shape[1]
    x_steps = np.arange(round(bbox_width/side) +1)
    n_x_steps = len(x_steps)
    x_step_len = bbox_width/n_x_steps

    if preview:
        fig, ax = plt.subplots(1,2)
        ax[0].imshow(img_data)
        ax[1].imshow(mask_data)


    count = 0
    colormap = cmr.take_cmap_colors('cmr.iceburn', n_x_steps*n_y_steps, cmap_range=(0.1, 0.9), return_fmt='hex')
    random.shuffle(colormap)

    for y_step in y_steps:
        shift_y = int(y_step*y_step_len)
        if shift_y > bbox_height:
                shift_y = bbox_height-side

        for x_step in x_steps:
            shift_x = int(x_step*x_step_len)
            if shift_x > bbox_width:
                    shift_x = bbox_width-side

            start_x = bbox[1]+shift_x
            start_y = bbox[0]+shift_y

            if start_x+side > img_data.shape[1]:
                    start_x = img_data.shape[1]-side
            if start_y+side > img_data.shape[0]:
                    start_y = img_data.shape[0]-side

            if preview:
                rect_left = patches.Rectangle((bbox[1]+shift_x, bbox[0]+shift_y), side, side, linewidth=1, edgecolor=colormap[count], facecolor='none')
                rect_right = patches.Rectangle((bbox[1]+shift_x, bbox[0]+shift_y), side, side, linewidth=1, edgecolor=colormap[count], facecolor='none')
                ax[0].add_patch(rect_left)
                ax[1].add_patch(rect_right)
                
                # ax[0].imshow(partial_img)
                # ax[1].imshow(partial_mask)
                # ax[1].imshow(mask_data)
            else:
                partial_img = img_data[start_y:start_y+side, start_x:start_x+side,:]
                partial_mask = mask_data[start_y:start_y+side, start_x:start_x+side]

                if remove_original_background:
                      partial_img = remove_background(partial_img, partial_mask)

                partial_img_ = Image.fromarray(partial_img)
                partial_mask_ = Image.fromarray(partial_mask.astype(np.uint8))

                partial_img_save_path = yaml_file["partial_img_folder"]
                partial_mask_save_path = yaml_file["partial_mask_folder"]

                partial_img_.save(os.path.join(partial_img_save_path, file_name + "_"+ image_month_extension + "part_{0}{1}".format(count, ending)))
                partial_mask_.save(os.path.join(partial_mask_save_path, file_name + "_"+ image_month_extension +  "part_{0}.png".format(count)))

            count += 1

    if preview:
        plt.show()

# ATTO
# yaml_file_name = "labelbox.yaml"
# yaml_file_name = "labelbox_tf_increase.yaml"
yaml_file_name = "labelbox_tf_increase_less_bkg.yaml"


# GROßGLOCKNER
# 2024
# yaml_file_name = "labelbox_gg_june24.yaml"
# yaml_file_name = "labelbox_gg_july24.yaml"
# yaml_file_name = "labelbox_gg_august24.yaml"
# yaml_file_name = "labelbox_gg_september24.yaml"

# 2025
# yaml_file_name = "labelbox_gg_june25.yaml"
# yaml_file_name = "labelbox_gg_july0425.yaml"
# yaml_file_name = "labelbox_gg_july3025.yaml"
# yaml_file_name = "labelbox_gg_august2625.yaml"
# yaml_file_name = "labelbox_gg_octobre1225.yaml"

# GRAZ
# yaml_file_name = "labelbox_graz.yaml"
# yaml_file_name = "labelbox_graz_june.yaml"
# yaml_file_name = "labelbox_graz_sep.yaml"

remove_bg = False

# if yaml_file_name == "labelbox.yaml":
#     remove_bg = True
# else:
#     remove_bg = False

with open(yaml_file_name) as f:
			yaml_file = yaml.safe_load(f)
			
save_folder = yaml_file["save_folder"]
img_folder = yaml_file["img_folder"]
mask_save_path = os.path.join(save_folder, "combined_masks")

# if yaml_file["ontology"] == "gg":
#     image_month_extension = yaml_file_name.split("_")[2].split(".")[0] + "_"
# else:

image_month_extension = ""

imgs = [ x for x in os.listdir(img_folder) if x.endswith('.JPG') or x.endswith('.jpg')]
split_size = yaml_file["split_size"]

for img in tqdm(imgs):
    # print(img)
    img_path = os.path.join(img_folder, img)
    file_name, file_extension = os.path.splitext(img)
    mask_path = os.path.join(mask_save_path, file_name + ".png")

    img_data = cv2.cvtColor(cv2.imread(img_path), cv2.COLOR_BGR2RGB)
    mask_data = np.array(Image.open(mask_path))
    create_sub_img(img_data, mask_data, file_name, file_extension, image_month_extension, side=split_size, remove_original_background=remove_bg)


    