import os
import numpy as np
from skimage.io import imread
import json
import pandas as pd

import matplotlib.pyplot as plt

def load_mask_images(directory):
    mask_images = []
    for filename in os.listdir(directory):
        if filename.endswith(".png") or filename.endswith(".jpg"):
            mask_images.append(imread(os.path.join(directory, filename)))
    return mask_images

def calculate_class_statistics(mask_images, ontology_path):
    class_counts = {}        
    with open(ontology_path) as f:
        ontology = json.load(f)
    
    class_names = list(ontology["ontology"].keys())
    class_counts = {}
    print("Class names: ", class_names)

    for mask in mask_images:
        unique, counts = np.unique(mask, return_counts=True)
        print("unique: ", unique)
        print("counts: ", counts)
        for u, c in zip(unique, counts):
            if u < len(class_names):  # Make sure the index is valid
                class_name = class_names[u]
                if class_name in class_counts:
                    class_counts[class_name] += c
                else:
                    class_counts[class_name] = c

    return ontology, class_counts

def plot_class_statistics(classes, percent, ontology):

    
    # Extract colors from ontology for each class
    colors = [ontology["ontology"][class_name].get("color", "#333333") for class_name in classes]
    
    # Create bar plot with specified colors
    plt.bar(classes, percent, color=colors)
    # Add percentage values above each bar
    for i, p in enumerate(percent):
        plt.text(i, p + 1, f'{p:.1f}%', ha='center')
    plt.xlabel('Class names')
    plt.ylabel('Percentage [%]')
    plt.ylim(0, 100)
    plt.title('Class Statistics')
    plt.show()


def get_latest_version(project):

    saved_datasets_path = "C:\\Users\\faulhamm\\Documents\\Philipp\\training\\{0}\\saved_datasets".format(project)
    versions = []
    for root, dirs, files in os.walk(saved_datasets_path):
        for dir in dirs:
            if dir.startswith("v"):
                versions.append(dir)
    
    sorted_versions = sorted(versions)
    latest_version = sorted_versions[-1]
    print("latest_version: ", latest_version)

    return latest_version

def get_class_statistics(class_counts):
    classes = list(class_counts.keys())
    counts = list(class_counts.values())

    percent = [c*100 / sum(counts) for c in counts]
    return classes, counts, percent

def create_df(classes, counts, percent):

    df = pd.DataFrame({"Class": classes, "Count": counts, "Percentage": percent})
    print(df)
    return df

def analyse_directories(parent_dir, ontology_path):

    with open(ontology_path) as f:
        ontology = json.load(f)
        

    main_df = pd.DataFrame(columns=["month"] + list(ontology["ontology"]))
    main_df = main_df.drop("fungi", axis=1)
    for p_dir, dirs, files in os.walk(parent_dir):
        for dir in dirs: 
            print("Directory: ", dir)
            month = dir.split("_")[-2]
            if month == "test":
                month = "july"
            directory = os.path.join(p_dir, dir)
            print(directory)
            mask_images = load_mask_images(directory)
            ontology, class_counts = calculate_class_statistics(mask_images, ontology_path)
            classes, counts, percent = get_class_statistics(class_counts)
            # df = create_df(classes, counts, percent)
            list_add = [month] + percent
            main_df = pd.concat([pd.DataFrame([list_add], columns=main_df.columns), main_df], ignore_index=True)           


    main_df.to_csv("monthly_stats.csv")


def analyse_masks(parent_dir, ontology_path):

    with open(ontology_path) as f:
        ontology = json.load(f)
    
    mask_dir = os.path.join(parent_dir, "combined_masks")
    mask_images = load_mask_images(mask_dir)
    ontology, class_counts = calculate_class_statistics(mask_images, ontology_path)
    classes, counts, percent = get_class_statistics(class_counts)
    # df = create_df(classes, counts, percent)
    plot_class_statistics(classes, percent, ontology)

    # df.to_csv("mask_stats.csv")

if __name__ == "__main__":

    # project = "cc_graz"
    project = "grossglockner"

    # version = get_latest_version(project)
    # directory = "C:\\Users\\faulhamm\\Documents\\Philipp\\training\\{0}\\saved_datasets\\{1}\\combined_masks".format(project, version)

    if project == "cc_graz":
        ontology_path = "C:\\Users\\faulhamm\\Documents\\Philipp\\code\\cc-data-processing\\ontology_graz.json"
        directory = "C:\\Users\\faulhamm\\Documents\\Philipp\\training\\cc_graz\\saved_datasets\\v4"
    elif project == "grossglockner":
        ontology_path = "C:\\Users\\faulhamm\\Documents\\Philipp\\code\\cc-data-processing\\ontology_gg.json"
        directory = "C:\\Users\\faulhamm\\Documents\\Philipp\\training\\grossglockner\\014_september_24"

    # directory = "C:\\Users\\faulhamm\\Documents\\Philipp\\Code\\cc-data-processing\\mask_analysis"
    
    # Analyse single directory (e.g. Graz, July 2024)
    analyse_masks(parent_dir=directory, ontology_path=ontology_path)

    # Analyse multiple directories (Großglockner, multiple months)
    # analyse_directories(parent_dir=directory, ontology_path=ontology_path)