import cv2
import numpy as np

img = cv2.imread("seat-maps/2026-07-30_13-00.png")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Let's count how many pixels are there for different blue masks
lower_1 = np.array([100, 100, 100])
upper_1 = np.array([130, 255, 255])
mask_1 = cv2.inRange(hsv, lower_1, upper_1)
print(f"Mask 1 (HSV blue): {np.sum(mask_1 > 0)} pixels")

# Let's see some contours of Mask 1
contours_1, _ = cv2.findContours(mask_1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
print(f"Mask 1 contours: {len(contours_1)}")
contours_1_sorted = sorted(contours_1, key=cv2.contourArea, reverse=True)
for i, c in enumerate(contours_1_sorted[:20]):
    print(f"Contour {i}: area={cv2.contourArea(c)}, arcLength={cv2.arcLength(c, True)}, bounding={cv2.boundingRect(c)}")
