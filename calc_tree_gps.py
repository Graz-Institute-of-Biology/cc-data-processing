import os
import pandas as pd

# folder = r"C:\Users\faulhamm\Documents\Philipp\Code\cc-data-processing\Tree_data"
folder = r"D:\Mavic-3-Fotos\ATTO"
output_path = r"C:\Users\faulhamm\Documents\Philipp\Code\cc-data-processing\Tree_data\tree_gps_data.csv"


def calc_mean_tree_gps(folder, output_path):
    gps_data = pd.DataFrame(columns=['tree_code', 'forest_type', 'mean_latitude', 'mean_longitude'])

    for root, dirs, files in os.walk(folder):
        if 'data_v2.csv' in files:

            folder_list = root.split(os.sep)[3:]
            parent_dir = os.path.basename(root)

            tree_code = "_".join(folder_list)
            tree_num = tree_code.split("_")[-1]
            try:
                int(tree_num)
            except ValueError:
                print("Skipping invalid tree folder: ", root)
                continue

            if "Sensor" in tree_code or "Overview" in tree_code:
                print("Skipping non-tree folder: ", root)
                continue

            if "Campina" in tree_code:
                forest_type = "C"
            else:
                forest_type = "F"

            filepath = os.path.join(root, 'data_v2.csv')
            df = pd.read_csv(filepath)
            print(f"Loaded: {filepath}")

            try:
                mean_lat = df['Latitude'].mean()
                mean_lon = df['Longitude'].mean()

                gps_data = pd.merge(gps_data, pd.DataFrame({
                    'tree_code': [tree_code],
                    'forest_type': [forest_type],
                    'mean_latitude': [mean_lat],
                    'mean_longitude': [mean_lon]
                }), how='outer', on=['tree_code', 'forest_type', 'mean_latitude', 'mean_longitude'])
            except KeyError as e:
                print(f"KeyError for file {filepath}: {e}")
                continue

    print(gps_data)
    output_path = os.path.join(output_path)
    gps_data.to_csv(output_path, index=False)


def get_tree_data(folder):
    tree_data = []
    for root, dirs, files in os.walk(folder):
        if 'data.csv' in files:
            date = os.path.basename(os.path.dirname(root))
            parent_dir = os.path.basename(root)

            tree_code = date + "_" + parent_dir
            tree_data.append(tree_code)
    return tree_data

def split_forest_types(output_path):
    df = pd.read_csv(output_path)
    forest_types = df['forest_type'].unique()

    for f_type in forest_types:
        subset_df = df[df['forest_type'] == f_type]
        if f_type == "C":
            f_type_name = "Campina"
        elif f_type == "F":
            f_type_name = "TerraFirme"

        subset_path = output_path.replace(".csv", f"_{f_type_name}.csv")
        subset_df.to_csv(subset_path, index=False)
        print(f"Saved subset for forest type {f_type} to {subset_path}")

if __name__ == "__main__":
    # calc_mean_tree_gps(folder, output_path)
    split_forest_types(output_path)
