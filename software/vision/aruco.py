"""
aruco.py - generate tokens for use with OpenCV

Generate ArUco markers for corner generation

References: https://www.geeksforgeeks.org/computer-vision/detecting-aruco-markers-with-opencv-and-python-1/

Modified to make 4 markers and save them locally for the four corners.
"""

import cv2
import os
import numpy as np
import matplotlib.pyplot as plt

# Define the ArUco dictionary
aruco_dict = cv2.aruco.getPredefinedDictionary(
    cv2.aruco.DICT_6X6_250
)

# make sure the directory exists
output_dir = "tokens"
os.makedirs(output_dir, exist_ok=True)

marker_id = 42
border = 20
marker_size = 200

corner_ids = [0, 1, 2, 3] 
corner_names = ["top_left", "top_right", "bottom_right", "bottom_left"]

fig, axes = plt.subplots(1, 4, figsize=(12, 3.5))

for ax, marker_id, name in zip(axes, corner_ids, corner_names):
    marker = cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_size)

    # Add a white margin around the marker
    image = np.ones(
        (marker_size + 2 * border, marker_size + 2 * border),
        dtype=np.uint8
    ) * 255
    image[border:border + marker_size, border:border + marker_size] = marker

    filename = os.path.join(output_dir, f"{name}.png")
    cv2.imwrite(filename, image)
    print(f"Saved {filename}")

    ax.imshow(image, cmap="gray")
    ax.set_title(f"{name}")
    ax.axis("off")

plt.tight_layout()
plt.show()