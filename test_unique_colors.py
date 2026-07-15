import cv2
import numpy as np

img = cv2.imread("seat-maps/2026-08-24_20-15.png")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

lower_blue = np.array([95, 200, 240])
upper_blue = np.array([110, 255, 255])
mask = cv2.inRange(hsv, lower_blue, upper_blue)

contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

centers = []
for cnt in contours:
    area = cv2.contourArea(cnt)
    x, y, w, h = cv2.boundingRect(cnt)
    if 35 <= area <= 100 and 7 <= w <= 15 and 7 <= h <= 15:
        centers.append((x + w//2, y + h//2))

# Let's count how many distinct colors we have in these detected seats
color_samples = []
for cx, cy in centers:
    # get the actual BGR value of the center pixel
    bgr = img[cy, cx].tolist()
    color_samples.append(bgr)

# Print unique colors and their frequency
from collections import Counter
counter = Counter(tuple(c) for c in color_samples)
print("Unique center pixel colors and their frequencies:")
for color, freq in counter.most_common():
    print(f"  BGR={color} (R={color[2]}, G={color[1]}, B={color[0]}): count={freq}")
