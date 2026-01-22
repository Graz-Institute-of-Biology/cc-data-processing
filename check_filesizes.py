import os
import matplotlib.pyplot as plt
import numpy as np

def plot_file_sizes_histogram(folder_path, type="jpg"):
    file_sizes = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if not file.endswith(type):
                continue
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            file_sizes.append(file_size)

    file_sizes_mb = np.array(file_sizes) / 1e6  # Convert file sizes to megabytes

    plt.hist(file_sizes_mb, bins=100)
    
    plt.xlabel('File Size (MB)')  # Update x-axis label
    plt.ylabel('Frequency')
    plt.title('Histogram of File Sizes | mean: {0:.2f} MB | median: {1:.2f} MB'.format(np.mean(file_sizes_mb), np.median(file_sizes_mb)))
    plt.show()

if __name__ == "__main__":
    # file_path = "C:\\Users\\faulhamm\\OneDrive - Universität Graz\\Dokumente\\Philipp\\Data\\Terra Firme"
    file_path = "C:\\Users\\faulhamm\\Documents\\Philipp\\Code\\cc-machine-learning\\test"
    plot_file_sizes_histogram(file_path, type="png")
