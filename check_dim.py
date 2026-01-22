from PIL import Image
import numpy as np
# Open the PNG file
# image = Image.open("C:\\Users\\faulhamm\\Documents\\Philipp\\Code\\cc-machine-learning\\mask_upload\\140223_TF_M_S_DJI_0528_mask_04.png")
image = Image.open("C:\\Users\\faulhamm\\Documents\\Philipp\\training\\grossglockner\\mask_upload\\3.4_mask.png")

# Print the dimensions
print(image.size)
print(np.asarray(image)[:100])