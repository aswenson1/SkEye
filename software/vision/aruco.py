"""
aruco.py - generate tokens for use with OpenCV

Generate ArUco markers for corner generation

References: https://www.geeksforgeeks.org/computer-vision/detecting-aruco-markers-with-opencv-and-python-1/
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt

# Define the ArUco dictionary
aruco_dict = cv2.aruco.getPredefinedDictionary(
    cv2.aruco.DICT_6X6_250
)

# Generate marker with ID 42
marker_id = 42
marker_size = 200

marker = cv2.aruco.generateImageMarker(
    aruco_dict, marker_id, marker_size
)

# Add a white margin around the marker
border = 20
image = np.ones(
    (marker_size + 2 * border, marker_size + 2 * border),
    dtype=np.uint8
) * 255

image[
    border:border + marker_size,
    border:border + marker_size
] = marker

# Display the generated marker
plt.imshow(image, cmap="gray")
plt.axis("off")
plt.show()