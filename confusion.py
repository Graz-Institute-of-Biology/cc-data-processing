from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from sklearn.preprocessing import normalize
from matplotlib import pyplot as plt
import pandas as pd
import os
import numpy as np
from PIL import Image

CLASS_VALUES = [0, 1, 2, 3, 4, 5, 6, 7, 8]
LABELS = ["background", "liverwort", "moss", "cyanosliverwort", "cyanosmoss", "lichen", "barkdominated", "cyanosbark", "other"]

def save_confusion_matrix(base_path):
    cf_matrix = np.zeros((len(CLASS_VALUES), len(CLASS_VALUES)))

    prediction_paths = [os.path.join(base_path, x) for x in os.listdir(base_path) if x.endswith("_no_bg_mask.png")]

    for pred_path in prediction_paths:
        
        gt_path = pred_path.replace("_no_bg_mask.png", ".png")
        print("GT: ", gt_path)
        print("PRED: ", pred_path)

        gt_mask_2d = np.array(Image.open(gt_path))
        unique_values = np.unique(gt_mask_2d)

        pred = np.array(Image.open(pred_path))

        y_pred_flattened = pred.flatten()
        y_true_flattened = gt_mask_2d.flatten()

        cf_m = confusion_matrix(y_true_flattened, y_pred_flattened)
        for i in range(len(unique_values)):
            u = unique_values[i]
            for j in range(len(unique_values)):
                k = unique_values[j]
                cf_matrix[u][k] += cf_m[i][j]


    cf_matrix_normed = normalize(cf_matrix, axis=1, norm='l1')
    disp = ConfusionMatrixDisplay(cf_matrix_normed, display_labels=LABELS)

    fig, ax = plt.subplots(figsize=(12, 12))
    disp.plot(ax=ax, xticks_rotation='vertical', colorbar=False)
    plt.colorbar(disp.im_, boundaries=np.linspace(0, 1, 11))
    plt.savefig("confusion_matrix.png")

    cfm_df = pd.DataFrame(columns=[LABELS], index=LABELS, data=cf_matrix_normed)
    cfm_df.to_csv("confusion_matrix.csv")


if __name__ == "__main__":

    # gt_path = "C:\\Users\\faulhamm\\Documents\\Philipp\\Code\\cc-machine-learning\\results\\train_tf_bg_removed\\analysis_no_bg\\difference\\130223_TF_M_E_DJI_0204.png"
    # pred_path = "C:\\Users\\faulhamm\\Documents\\Philipp\\Code\\cc-machine-learning\\results\\train_tf_bg_removed\\analysis_no_bg\\130223_TF_M_E_DJI_0204_no_bg_mask.png"
    base_path = "C:\\Users\\faulhamm\\Documents\\Philipp\\Code\\cc-machine-learning\\results\\train_tf_bg_removed\\analysis_no_bg\\difference"
    save_confusion_matrix(base_path)