import cv2
import numpy as np

img = cv2.imread("seat-maps/2026-07-30_13-00.png")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Mask for #4790D2 or similar (B in 150-255, G in 80-180, R in 30-100)
# Or in HSV:
# Let's use BGR thresholding directly since it's very distinct and consistent.
# B: 150 to 255, G: 80 to 180, R: 30 to 110
lower_blue = np.array([140, 80, 30])
upper_blue = np.array([255, 180, 110])
mask = cv2.inRange(img, lower_blue, upper_blue)

# Find connected components or contours
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
print(f"Total contours found: {len(contours)}")

valid_circles = []
for i, cnt in enumerate(contours):
    area = cv2.contourArea(cnt)
    # Let's get the bounding box or minimum enclosing circle
    (x, y), radius = cv2.minEnclosingCircle(cnt)
    center = (int(x), int(y))
    radius = int(radius)
    
    # Calculate circularity: 4 * pi * area / perimeter^2
    perimeter = cv2.arcLength(cnt, True)
    circularity = (4 * np.pi * area) / (perimeter ** 2) if perimeter > 0 else 0
    
    # Let's print properties of some contours
    if i < 15:
        print(f"Contour {i}: area={area:.1f}, radius={radius:.1f}, circularity={circularity:.2f}, center={center}")
        
    # Blue seat circles are very small.
    # In the screenshot, they have a radius of around 3 to 6 pixels.
    # Area should be around pi * r^2 (e.g. pi * 4^2 = 50, pi * 5^2 = 78)
    if 5 <= area <= 120:
        valid_circles.append((center, radius, area, circularity))

print(f"Valid circles with area between 5 and 120: {len(valid_circles)}")
