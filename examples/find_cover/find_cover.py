import os
from PIL import Image
import numpy as np
import cv2
from rembg import remove

def order_points(pts):
    # Initialize ordered points
    rect = np.zeros((4, 2), dtype=np.float32)
    
    # Top-left point will have the smallest sum
    # Bottom-right point will have the largest sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    # Top-right point will have the smallest difference
    # Bottom-left point will have the largest difference
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    return rect

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

# Load and remove background
input_path = 'examples/find_cover/cover1.jpg'
img = Image.open(input_path)
output = remove(img)
output.save('examples/find_cover/debug_without_cover.png')

# Convert to OpenCV format for contour detection
img_cv = cv2.cvtColor(np.array(output), cv2.COLOR_RGBA2BGRA)
gray = cv2.cvtColor(img_cv, cv2.COLOR_BGRA2GRAY)

# Find contours
contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

if contours:
    # Find the largest contour
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Approximate the contour to get a polygon
    epsilon = 0.02 * cv2.arcLength(largest_contour, True)
    approx = cv2.approxPolyDP(largest_contour, epsilon, True)
    
    if len(approx) == 4:
        # Get dimensions for the output image
        # Use maximum of width and height to determine orientation
        width = int(max(
            np.linalg.norm(approx[0] - approx[1]),
            np.linalg.norm(approx[2] - approx[3])
        ))
        height = int(max(
            np.linalg.norm(approx[1] - approx[2]),
            np.linalg.norm(approx[3] - approx[0])
        ))
        
        # Swap width and height if the image is in portrait orientation
        if width > height:
            width, height = height, width

        # Define destination points for perspective transform
        dst_points = np.array([
            [0, 0],
            [width-1, 0],
            [width-1, height-1],
            [0, height-1]
        ], dtype=np.float32)
        
        # Sort source points for correct mapping
        src_points = np.float32(approx.reshape(4, 2))
        src_points = order_points(src_points)
        
        # Apply perspective transformation
        matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        result = cv2.warpPerspective(img_cv, matrix, (width, height))
        
        # Convert back to correct color space before saving
        result_bgr = cv2.cvtColor(result, cv2.COLOR_BGRA2BGR)
        
        # Save result
        cv2.imwrite('examples/find_cover/output.jpg', result_bgr)

