import cv2
import numpy as np

img = cv2.imread("seat-maps/2026-07-30_13-00.png")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Available seats we found:
avail_coords = [(149, 595), (581, 583), (643, 602)]

print("--- AVAILABLE SEATS (BRIGHT BLUE) ---")
for cx, cy in avail_coords:
    # let's print BGR and HSV of a 3x3 region around center
    bgr_sample = img[cy-1:cy+2, cx-1:cx+2]
    hsv_sample = hsv[cy-1:cy+2, cx-1:cx+2]
    print(f"Seat at ({cx}, {cy}):")
    print(f"  BGR: B={bgr_sample[:,:,0].mean():.1f}, G={bgr_sample[:,:,1].mean():.1f}, R={bgr_sample[:,:,2].mean():.1f}")
    print(f"  HSV: H={hsv_sample[:,:,0].mean():.1f}, S={hsv_sample[:,:,1].mean():.1f}, V={hsv_sample[:,:,2].mean():.1f}")

print("\n--- TAKEN SEATS (LIGHT PURPLE/GRAY) ---")
# Let's find some taken seats. From the image, they are at the top rows, e.g., around row Q center.
# Let's search for circles that are NOT the three available ones.
# Let's find any other gray/purple dots. We can use a very broad mask first.
lower_any_dot = np.array([0, 10, 100])
upper_any_dot = np.array([180, 255, 255])
broad_mask = cv2.inRange(hsv, lower_any_dot, upper_any_dot)
contours, _ = cv2.findContours(broad_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

taken_count = 0
for cnt in contours:
    area = cv2.contourArea(cnt)
    if 35 <= area <= 100:
        mom = cv2.moments(cnt)
        if mom["m00"] != 0:
            cx = int(mom["m10"] / mom["m00"])
            cy = int(mom["m01"] / mom["m00"])
            # Check if it's near one of the available ones
            if any(abs(cx - ax) < 15 and abs(cy - ay) < 15 for ax, ay in avail_coords):
                continue
            
            # Print BGR/HSV of this taken seat
            bgr_sample = img[cy-1:cy+2, cx-1:cx+2]
            hsv_sample = hsv[cy-1:cy+2, cx-1:cx+2]
            print(f"Taken seat at ({cx}, {cy}):")
            print(f"  BGR: B={bgr_sample[:,:,0].mean():.1f}, G={bgr_sample[:,:,1].mean():.1f}, R={bgr_sample[:,:,2].mean():.1f}")
            print(f"  HSV: H={hsv_sample[:,:,0].mean():.1f}, S={hsv_sample[:,:,1].mean():.1f}, V={hsv_sample[:,:,2].mean():.1f}")
            taken_count += 1
            if taken_count >= 5:
                break
