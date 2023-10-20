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


def get_props(mask_data):
    mask_data_ = mask_data.copy()
    mask_data_[mask_data > 0] = 1
    return measure.regionprops(mask_data_)

def create_sub_img(img_data, mask_data, img_path, side=1024, preview=False):

    props = get_props(mask_data)
    bbox = props[0].bbox
    # print(img_data.shape)
    # print(bbox)

    bbox_new = np.array(bbox)
    if bbox[1] - side/2 > 0:
        bbox_new[1] = int(bbox[1] - side/2)
    else:
        bbox_new[1] = 0
    
    if bbox[0] - side/2 > 0:
        bbox_new[0] = int(bbox[0] - side/2)
    else:
        bbox_new[0] = 0

    bbox = tuple(bbox_new)

    bbox_height = bbox[2]-bbox[0]
    y_steps = np.arange(round(bbox_height/side))
    n_y_steps = len(y_steps)
    y_step_len = bbox_height/n_y_steps

    bbox_width = bbox[3]-bbox[1]
    x_steps = np.arange(round(bbox_width/side) +1)
    n_x_steps = len(x_steps)
    x_step_len = bbox_width/n_x_steps

    if preview:
        fig, ax = plt.subplots(1,2)
        ax[0].imshow(img_data)
        ax[1].imshow(mask_data)

    else:
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
                    partial_img_ = Image.fromarray(partial_img)
                    partial_mask_ = Image.fromarray(partial_mask.astype(np.uint8))
                    
                    partial_img_save_path = yaml_file["partial_img_folder"]
                    partial_mask_save_path = yaml_file["partial_mask_folder"]

                    partial_img_.save(os.path.join(partial_img_save_path, img_path.replace(".JPG","_part_{0}.JPG".format(count))))
                    print(partial_img_.size)
                    partial_mask_.save(os.path.join(partial_mask_save_path, img_path.replace(".JPG","_part_{0}.png".format(count))))
                    print(partial_mask_.size)

                count += 1

    if preview:
        plt.show()

yaml_file="labelbox.yaml"
with open(yaml_file) as f:
			yaml_file = yaml.safe_load(f)
			
save_folder = yaml_file["save_folder"]
img_folder = yaml_file["img_folder"]
mask_save_path = os.path.join(save_folder, "combined_masks")

imgs = os.listdir(img_folder) 

for img in imgs:
    side = 1024
    print(img)
    img_path = os.path.join(img_folder, img)
    mask_path = os.path.join(mask_save_path, img.replace(".JPG", ".png"))

    img_data = cv2.cvtColor(cv2.imread(img_path), cv2.COLOR_BGR2RGB)
    mask_data = np.array(Image.open(mask_path))
    create_sub_img(img_data, mask_data, img, side=side)


    