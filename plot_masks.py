import numpy as np
from matplotlib import pyplot as plt
import os
from PIL import Image
from matplotlib.colors import ListedColormap, BoundaryNorm
import matplotlib.patches as mpatches

######################################################################################################################
### Atto:
# class_dict_atto = {	    "background" : 0,
#                                 "liverwort" : 1,
# 								"moss" : 2,
# 								"cyanosliverwort" : 3,
# 								"cyanosmoss" : 4,
# 								"lichen" : 5,
# 								"barkdominated" : 6,
# 								"cyanosbark" : 7,
# 								"other" : 8,
#                             }
# colors_hex_atto = ["#000000","#1cffbb", "#00bcff","#0059ff", "#2601d8", "#ff00c3", "#FF4A46", "#ff7500", "#928e00"]

######################################################################################################################

### Grossglockner:
class_dict = {
                "background" : 0,	
                "cyano_-_dominated" : 1,
                "lichen" : 2,
                "moss" : 3,
                "vascular plants" : 4,
                "rock" : 5,
                "other" : 6,
                "fungi" : 7,
                "markers" : 8,
                "snow": 9,
            }
            
colors_hex = ["#000000","#1CE6FF","#ffdb0c","#FF4A46","#008941","#dc22e6","#B79762","#7A4900","#FFDBE5", "#8FB0FF"]

######################################################################################################################

## graz:

# class_dict = {
#                 "background" : 0,
#                 "bryophyte" : 1,
#                 "lichen" : 2,
#                 "barkdominated" : 3,
#                 "other" : 4,
# 			}

# colors_hex = ["#000000","#1CE6FF","#FF34FF","#FF4A46","#928e00"]


def plot_save_mask(mask_path, save_path):

    mask = np.array(Image.open(mask_path))
    labels = list(class_dict.keys())
    print(np.unique(mask))

    col = ListedColormap(colors_hex)
    bounds = np.arange(len(colors_hex)+1)
    norm = BoundaryNorm(bounds, col.N)  

    # fig = plt.figure(figsize=mask.shape[::-1], dpi=1)
    fig = plt.figure(figsize=(mask.shape[1]/20, mask.shape[0]/20), dpi=20)
    # fig = plt.figure()

    fig.subplots_adjust(bottom = 0)
    fig.subplots_adjust(top = 1)
    fig.subplots_adjust(right = 1)
    fig.subplots_adjust(left = 0)
    
    plt.imshow(mask, cmap=col, interpolation='nearest', norm=norm)
    patches = [mpatches.Patch(color=colors_hex[i], label=labels[i] ) for i in np.unique(mask)]
    plt.axis('off')
    plt.legend(handles=patches, bbox_to_anchor=(1, 1), loc=0, borderaxespad=0., fontsize=200)
    # plt.show()
    plt.savefig(save_path.replace("_04.png", "_mask_04.png"))
    plt.close()




if __name__ == "__main__":

    input_path =r"C:\Users\faulhamm\Documents\Philipp\Code\cc-machine-learning\results\02-cc-gg\test_gg_climatechamber_135"
    output_path = r"C:\Users\faulhamm\Documents\Philipp\Code\cc-machine-learning\results\02-cc-gg\test_gg_climatechamber_135"

    # test_path = "C:\\Users\\faulhamm\\Documents\\Philipp\\training\\grossglockner\\mask_upload"
    # comp_path = "C:\\Users\\faulhamm\\Documents\\Philipp\\training\\grossglockner\\mask_upload"

    # mask_files = [x for x in os.listdir(test_path) if x.endswith("mask.png")]
    mask_files = [x for x in os.listdir(input_path) if x.endswith("mask.png")]


    # test_path = "C:\\Users\\faulhamm\\Documents\\Philipp\\Code\\cc-machine-learning\\results\\train_tf_bg_removed\\analysis_no_bg"
    # comp_path = "C:\\Users\\faulhamm\\Documents\\Philipp\\Code\\cc-machine-learning\\results\\train_tf_bg_removed\\analysis_no_bg"
    # mask_files = [x for x in os.listdir(test_path) if x.endswith("mask.png")]
    # entropy_files = [x for x in os.listdir(test_path) if x.endswith("entropy.png")]

    total_files = len(mask_files)
    count = 1

    for mask_file in mask_files:
        mask_path = os.path.join(input_path, mask_file)
        print("{0} / {1} | {2}".format(count, total_files, mask_path))
        # save_path = os.path.join(comp_path, mask_file.replace(".png", "_mask_GT.png"))
        save_path = os.path.join(output_path, mask_file.replace("mask.png", "vis.png"))
        # save_path = os.path.join(comp_path, mask_file.replace(".jpg", "_vis.png"))
        plot_save_mask(mask_path, save_path)
        count += 1


    # for entropy_file in entropy_files:
    #     entropy_path = os.path.join(test_path, entropy_file)
    #     new_entropy_path = os.path.join(comp_path, entropy_file.replace("_entropy.png", "_entropy.png"))
    #     os.rename(entropy_path, new_entropy_path) 