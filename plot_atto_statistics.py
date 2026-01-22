import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import numpy as np
from collections import Counter
# import seaborn as sns
# sns.set_context('talk')

def plot_save_statistics(df, save_path=None):
    x_axis = ['N', 'E', 'S', 'W']
    x=np.arange(len(x_axis))
    fig, ax = plt.subplots(3,1, figsize=(8,10))

    bar_width = 0.3
    b1 = ax[2].bar(x, df.values[0][:4], width=bar_width, label="Terra firme")
    b2 = ax[2].bar(x + bar_width, df.values[0][12:16], width=bar_width, label="Campina")
    ax[2].set_title("Ground")

    b3 = ax[1].bar(x, df.values[0][4:8], width=bar_width, label="Terra firme")
    # b2 = ax[0].bar(x + bar_width, df.values[0][12:16], width=bar_width)
    ax[1].set_title("Main stem")

    b5 = ax[0].bar(x, df.values[0][8:12], width=bar_width, label="Terra firme")
    b6 = ax[0].bar(x + bar_width, df.values[0][16:], width=bar_width, label="Campina")
    ax[0].set_title("Canopy")


    for a in ax:
        a.set_xticks(x + bar_width / 2)
        a.set_xticklabels(x_axis)
        a.set_ylabel('# Images', labelpad=15)
        a.legend()

    ax[2].set_xlabel('Direction', labelpad=15)


    # plt.savefig("C:\\Users\\faulhamm\\Documents\\Philipp\\code\\cc-data-processing\\microhabitats.png", dpi=300, bbox_inches='tight')
    plt.show()

def get_statistics_from_masks(mask_path):
    file_names = os.listdir(mask_path)
    tf_microhabitat_codes = [("-").join(f.split("_")[1:4]) for f in file_names if f.split("_")[1] == "TF"]
    c_microhabitat_codes = [("-").join(f.split("_")[1:4]) for f in file_names if f.split("_")[1] == "C"]
    # c_microhabitat_codes.extend(["C-M-S", "C-M-E", "C-M-N", "C-M-W", "C-C-S", "C-C-E", "C-C-N", "C-C-W"])

    # Convert string categories to numerical values
    categories_tf = sorted(list(set(tf_microhabitat_codes)))  # Get unique categories
    category_counts_tf = [tf_microhabitat_codes.count(category) for category in categories_tf]

    categories_c = list(set(c_microhabitat_codes))  # Get unique categories
    categories_c.extend(["C-M-S", "C-M-E", "C-M-N", "C-M-W", "C-C-S", "C-C-E", "C-C-N", "C-C-W"])
    categories_c = sorted(categories_c)
    category_counts_c = [c_microhabitat_codes.count(category) for category in categories_c]

    # Create a counter with zero counts for all categories
    counter_with_zeros_c = Counter({category: 0 for category in categories_c})
    counter_with_zeros_c.update(c_microhabitat_codes)

    # Extract categories and corresponding counts
    categories_c = list(counter_with_zeros_c.keys())
    category_counts_c = list(counter_with_zeros_c.values())

    # Plot histogram
    fig, ax = plt.subplots(2, 1, figsize=(12, 8))
    ax[0].bar(categories_tf, category_counts_tf, color='skyblue')
    ax[0].set_xlabel('Microhabitats')
    ax[0].set_ylabel('Counts')
    ax[0].set_title('Histogram of Microhabitats in Terra Firme')

    ax[1].bar(categories_c, category_counts_c, color='skyblue')
    ax[1].set_xlabel('Microhabitats')
    ax[1].set_ylabel('Counts')
    ax[1].set_title('Histogram of Microhabitats in Campina')
    # plt.ylim(0, 20)
    plt.tight_layout()
    plt.show()



if __name__ == "__main__":
    # df = pd.read_csv("C:\\Users\\faulhamm\\Documents\\Philipp\\code\\cc-data-processing\\microhabitats.csv")
    # mask_path = "C:\\Users\\faulhamm\\Documents\\Philipp\\labelbox_data\\combined_masks"
    mask_path = "C:\\Users\\faulhamm\\Documents\\Philipp\\training\\cc_graz\\saved_datasets\\v2\\combined_masks"
    df = get_statistics_from_masks(mask_path)
    # print(df.values[0])
    plot_save_statistics(df)