import os
import yaml
from PIL import Image
from matplotlib import pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap, BoundaryNorm
import matplotlib.patches as mpatches
from PIL import ImageColor
from tqdm import tqdm


class_codes = {	"background" : 0,
	            "liverwort" : 1,
                "moss" : 2,
                "cyanosliverwort" : 3,
                "cyanosmoss" : 4,
                "lichen" : 5,
                "barkdominated" : 6,
                "cyanosbark" : 7,
                "other" : 8,}

labels = list(class_codes.keys())
colors_hex = ["#000000","#1cffbb", "#00bcff","#0059ff", "#2601d8", "#ff00c3", "#FF4A46", "#ff7500", "#928e00"]
colors = [ImageColor.getcolor(c, "RGB") for c in colors_hex]
print(colors)
col = ListedColormap(colors_hex)
bounds = np.arange(len(labels))
norm = BoundaryNorm(bounds, col.N)
print(col)
print(labels)

def plot_img(img):
    plt.figure()
    plt.imshow(img, cmap=col, norm=norm)
    patches = [ mpatches.Patch(color=colors_hex[i], label=labels[i] ) for i in np.unique(img).astype(int)]
    plt.axis('off')
    plt.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc=0, borderaxespad=0. )
    plt.show()  



# print(list(col))

yaml_file="labelbox.yaml"
with open(yaml_file) as f:
			yaml_file = yaml.safe_load(f)
			
save_folder = yaml_file["save_folder"]
mask_save_path = os.path.join(save_folder, "combined_masks")

mask_paths = os.listdir(mask_save_path)

mask_path_partial = "C:\\Users\\faulhamm\\Documents\\Philipp\\training\\partial_masks\\1024"
# mask_abs_paths = [os.path.join(mask_save_path, f) for f in mask_paths]
mask_abs_paths = [os.path.join(mask_path_partial, f) for f in os.listdir(mask_path_partial)]

# calculate mean value from RGB channels and flatten to 1D array
# plot histogram with 255 bins

# print(np.unique(im))
bins=[0,1,2,3,4,5,6,7,8]
total_counts = np.zeros(len(class_codes.keys()), dtype=int)

for mask in tqdm(mask_abs_paths):
    counts = np.zeros(len(class_codes.keys()), dtype=int)
    img = np.array(Image.open(mask))
    # plot_img(img)
    bincount = np.bincount(img.flatten())
    counts[:len(bincount)] = bincount
    total_counts += counts

colors_hex = ["#000000","#1cffbb", "#00bcff","#0059ff", "#2601d8", "#ff00c3", "#FF4A46", "#ff7500", "#928e00"]

total_bins = sum(total_counts[1:])
fig, ax = plt.subplots(figsize=(12,6))
fig.suptitle("Class distribution of CC [Image crops: {0}]".format(len(mask_abs_paths)))
plt.ylim(0,100)
plt.xlabel("Classes")
plt.ylabel("Percentage of total pixels [%]")
ax.bar(list(class_codes.keys())[1:], total_counts[1:]/total_bins*100, color=colors_hex[1:])
ax.bar_label(ax.containers[0], label_type='edge')
plt.show()