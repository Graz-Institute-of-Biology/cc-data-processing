import cv2
import matplotlib.pyplot as plt

# Read the image
image = cv2.imread('data/overview_marked.JPG')

# Get the dimensions of the image
height, width, _ = image.shape

# Calculate the midpoint of the image
midpoint = (int(width/2), int(height/2))

# Calculate the radius based on drone height and radial distance
drone_height = 250  # meters
radial_distance = 50  # meters
pixel_size = drone_height / height  # meters per pixel
radius = int(radial_distance / pixel_size)

# Draw circles on the image with increasing radii
circle_color = (0, 255, 0)  # Green color
circle_thickness = 2  # Outline thickness
circle_center_points = [midpoint]

for r in range(50, radius, 50):
    cv2.circle(image, midpoint, r, circle_color, circle_thickness)

# Plot the modified image
plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
plt.show()
