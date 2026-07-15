import cv2
import numpy as np

img = cv2.imread("seat-maps/2026-08-24_14-00.png")
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

# Let's check distances between any two centers
close_pairs = 0
for i in range(len(centers)):
    for j in range(i+1, len(centers)):
        dist = np.hypot(centers[i][0] - centers[j][0], centers[i][1] - centers[j][1])
        if dist < 8:
            close_pairs += 1

print(f"Total detected centers: {len(centers)}")
print(f"Number of center pairs closer than 8 pixels: {close_pairs}")
