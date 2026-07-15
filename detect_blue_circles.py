"""Detect all available blue seats in the saved seat plan images.

This script:
  1. Finds all PNG files in the `seat-maps/` directory.
  2. Applies a color mask to locate the bright blue available seats.
  3. Finds contours and filters them by area and shape to identify circles.
  4. Saves an annotated image with red circles around the detected seats to `seat-maps-annotated/`.
  5. Saves a JSON report (`detected-seats.json`) containing the seat coordinates and counts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

SEAT_MAP_DIR = Path("seat-maps")
ANNOTATED_DIR = Path("seat-maps-annotated")


def detect_seats(img_path: Path) -> list[tuple[int, int]]:
    """Detect blue seats in an image. Returns a list of (x, y) coordinates of centers."""
    img = cv2.imread(str(img_path))
    if img is None:
        print(f"[!] Could not read image: {img_path}", file=sys.stderr)
        return []

    # Convert to HSV for robust color segmentation
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Tight range for the bright blue seats
    lower_blue = np.array([95, 100, 100])
    upper_blue = np.array([135, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    centers = []
    annotated = img.copy()

    for cnt in contours:
        area = cv2.contourArea(cnt)
        # Bounding rect
        x_box, y_box, w_box, h_box = cv2.boundingRect(cnt)

        # Filter:
        # - Available seat dots are typically ~10-11px wide/tall with area ~60-75
        # - We use slightly broader thresholds to ensure we capture all of them
        if 35 <= area <= 100 and 7 <= w_box <= 15 and 7 <= h_box <= 15:
            # Calculate the center of the contour using moments
            mom = cv2.moments(cnt)
            if mom["m00"] != 0:
                cx = int(mom["m10"] / mom["m00"])
                cy = int(mom["m01"] / mom["m00"])
            else:
                cx = x_box + w_box // 2
                cy = y_box + h_box // 2

            centers.append((cx, cy))

            # Draw circle on annotated image
            cv2.circle(annotated, (cx, cy), 8, (0, 0, 255), 2)  # Red circle around blue dot
            cv2.drawMarker(annotated, (cx, cy), (0, 0, 255), cv2.MARKER_CROSS, 4, 1)

    # Add text banner with count
    count = len(centers)
    cv2.putText(
        annotated,
        f"Available seats: {count}",
        (15, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 255),
        2,
        cv2.LINE_AA,
    )

    # Save annotated image
    out_path = ANNOTATED_DIR / img_path.name
    cv2.imwrite(str(out_path), annotated)

    return centers


def main() -> int:
    if not SEAT_MAP_DIR.exists():
        print(f"[!] {SEAT_MAP_DIR} directory does not exist. Run scrape/screenshots first.", file=sys.stderr)
        return 1

    ANNOTATED_DIR.mkdir(exist_ok=True)

    png_files = sorted(list(SEAT_MAP_DIR.glob("*.png")))
    if not png_files:
        print("[!] No PNG images found in seat-maps/")
        return 1

    print(f"Processing {len(png_files)} seat map images...\n")
    results = {}

    for i, path in enumerate(png_files):
        # Filename is typically YYYY-MM-DD_HH-MM.png
        dt_str = path.stem.replace("_", " ")
        centers = detect_seats(path)
        count = len(centers)
        results[path.stem] = {
            "datetime": dt_str,
            "filename": path.name,
            "count": count,
            "seats": [{"x": cx, "y": cy} for cx, cy in centers],
        }
        print(f"  [{i+1:>2}/{len(png_files)}] {dt_str:<18} -> {count:>3} available seats detected")

    # Save JSON report
    with open("detected-seats.json", "w") as f:
        json.dump(results, f, indent=2)

    total_seats = sum(res["count"] for res in results.values())
    print("\n" + "=" * 60)
    print(f"Circle Detection Complete!")
    print(f"Total available seats across all viewings: {total_seats}")
    print(f"Annotated images saved to: {ANNOTATED_DIR}/")
    print(f"JSON report saved to:      detected-seats.json")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
