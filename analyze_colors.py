"""Sample pixel colors from the seat map to understand the color palette of seats vs background."""

import cv2
import numpy as np

img = cv2.imread("seat-maps/2026-08-10_12-00.png")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Sample colors at known blue seat locations (from detected-seats.json)
blue_seats = [
    (123, 602), (642, 601), (135, 598), (630, 597),
    (148, 594), (618, 593), (161, 590), (605, 590),
]

print("=== Blue (available) seats ===")
for x, y in blue_seats:
    bgr = img[y, x]
    hsv_val = hsv[y, x]
    print(f"  ({x},{y}): BGR={bgr}, HSV={hsv_val}")

# Sample colors at empty positions (not detected as blue) between seats
# These should be sold/unavailable seats or background
print("\n=== Sampling non-blue positions in seat area ===")
# Scan the seat map area for pixel colors
for y in [602, 590, 578, 565, 545, 520, 490, 460, 420, 380, 340, 310]:
    for x in range(100, 680, 20):
        bgr = img[y, x]
        hsv_val = hsv[y, x]
        # Only print if it's not blue (available) - H not in 90-130 range
        if not (90 < hsv_val[0] < 130):
            print(f"  ({x},{y}): BGR={bgr}, HSV={hsv_val}")

# Build a color histogram of the seat area
print("\n=== Color histogram of seat area ===")
seat_area = hsv[290:620, 90:680]
# Quantize H into 18 bins (20 degrees each), S into 4, V into 4
h_bins = 18
s_bins = 4
v_bins = 4
hist = np.zeros((h_bins, s_bins, v_bins))
for y in range(seat_area.shape[0]):
    for x in range(seat_area.shape[1]):
        h_val = int(seat_area[y, x, 0] / 180 * h_bins) % h_bins
        s_val = min(int(seat_area[y, x, 1] / 256 * s_bins), s_bins - 1)
        v_val = min(int(seat_area[y, x, 2] / 256 * v_bins), v_bins - 1)
        hist[h_val, s_val, v_val] += 1

# Print top color bins
flat = hist.reshape(-1)
top_idx = np.argsort(flat)[::-1][:20]
print("Top 20 color bins (H_bin, S_bin, V_bin) -> count:")
for idx in top_idx:
    h = idx // (s_bins * v_bins)
    s = (idx % (s_bins * v_bins)) // v_bins
    v = idx % v_bins
    h_range = f"{h*10}-{(h+1)*10}"
    s_range = f"{s*64}-{(s+1)*64}"
    v_range = f"{v*64}-{(v+1)*64}"
    print(f"  H={h_range}, S={s_range}, V={v_range}: {int(flat[idx])} pixels")
