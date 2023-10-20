from matplotlib import pyplot as plt
import os
from PIL import Image
import numpy as np

base_path = "C:\\Users\\faulhamm\\Documents\\Philipp\\training\\partial_masks\\2048"

file_names = os.listdir(base_path)

a = np.zeros(())

for file_name in file_names:

    img = Image.open(os.path.join(base_path, file_name))
    np_frame = np.array(img)
    u = np.unique(np_frame)
    print(file_name)
    print("Values:")
    print(u)
    a.append(u)
    # plt.figure()
    # plt.imshow(np_frame)
    # plt.show()

print(np.unique(np.array(a)))