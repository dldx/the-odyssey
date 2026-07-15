import cv2
import numpy as np

for filename in ["2026-07-30_13-00.png", "2026-08-24_20-15.png"]:
    img = cv2.imread(f"seat-maps/{filename}")
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Very high saturation (>= 200) and brightness (>= 240)
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
            
    print(f"File: {filename} -> found {len(centers)} seats with tight Saturation/Value threshold")
