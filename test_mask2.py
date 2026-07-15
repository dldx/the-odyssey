import cv2
import numpy as np
from pathlib import Path

img_path = Path("seat-maps/2026-08-24_20-15.png")
if not img_path.exists():
    # find any other PNG file in seat-maps/
    for p in Path("seat-maps").glob("*.png"):
        img_path = p
        break

print(f"Testing {img_path}")
img = cv2.imread(str(img_path))
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Mask for bright blue
lower_blue = np.array([100, 100, 100])
upper_blue = np.array([130, 255, 255])
mask = cv2.inRange(hsv, lower_blue, upper_blue)

contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
print(f"Total contours: {len(contours)}")

# Sort and print non-zero area contours
valid = []
for i, c in enumerate(contours):
    area = cv2.contourArea(c)
    if area > 10:
        bounding = cv2.boundingRect(c)
        valid.append((area, bounding))

valid = sorted(valid, key=lambda x: x[0], reverse=True)
print(f"Contours with area > 10: {len(valid)}")
for i, (area, bounding) in enumerate(valid[:30]):
    print(f"  {i}: area={area}, bounding={bounding}")
