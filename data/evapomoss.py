import pandas as pd
from matplotlib import pyplot as plt

def time_diff_hours(t, t0):
    hours = (t - t0).total_seconds() // 3600
    return hours


def plot_df(df):
    time = [t for t in df[list(df)[0]].values]
    tree_names = ["Tree 1 Ground", "Tree 1 Canopy", "Tree 2 Ground", "Tree 2 Canopy"]
    
    for ind, key in enumerate(list(df)[1:]):
        # normalize to initial value
        vals = df[key].values # / df[key].values[0]

        if ind%4 == 0:
            fig, ax = plt.subplots()
            plt.suptitle(tree_names[ind//4])
        # plt.scatter(time, vals, label=key)
        plt.plot(time, vals, label=key)
        plt.xlabel("Times points")
        plt.ylabel("Water weight [g]")
        ax.xaxis.set_major_locator(plt.MaxNLocator(20))
        plt.xticks(rotation=90)
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

    plt.show()

# Specify the path to your XLSX file
# xlsx_file = 'C:\\Users\\faulhamm\\OneDrive - Universität Graz\\Dokumente\\Philipp\\PhD - Institut Biologie\\ATTO\\Data\\2024\\EvapoMoss\\measurements.xlsx'
csv_file = 'C:\\Users\\faulhamm\\Documents\\Philipp\\Code\\cc-data-processing\\data\\EvapoMossAllDaysWater.csv'

# Read the XLSX file into a Pandas DataFrame
# df = pd.read_excel(xlsx_file)
df = pd.read_csv(csv_file)

# Now you can work with the DataFrame as needed
# For example, you can print the first few rows
print(df.head())
print("Mean: ", df.drop(['TimeStamp'], axis=1).mean().mean())
print("Std: ", df.drop(['TimeStamp'], axis=1).mean().std())
print("Min: ", df.drop(['TimeStamp'], axis=1).min().min())
print("Max: ", df.drop(['TimeStamp'], axis=1).max().max())

plot_df(df)




