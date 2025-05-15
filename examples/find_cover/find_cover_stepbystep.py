import cv2
import numpy as np
from rembg import remove

def find_book_cover(image_path, output_path):
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        raise Exception(f"Failed to open {image_path}")
    original = image.copy()
    print(f"[DEBUG] Image loaded: {image.shape}")
    cv2.imwrite("step-by-step\\debug_01_original.jpg", image)

    # Edge detection
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cv2.imwrite("step-by-step\\debug_02_gray.jpg", gray)
    
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    cv2.imwrite("step-by-step\\debug_03_blurred.jpg", blurred)
    
    edges = cv2.Canny(blurred, 75, 200)
    cv2.imwrite("step-by-step\\debug_04_edges.jpg", edges)
    print("[DEBUG] Edges detected")
    
    # Enhance edges
    kernel = np.ones((5,5), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)
    cv2.imwrite("step-by-step\\debug_05_dilated.jpg", edges)
    edges = cv2.erode(edges, kernel, iterations=1)
    cv2.imwrite("step-by-step\\debug_06_eroded.jpg", edges)
    print("[DEBUG] Morphological processing completed")

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(f"[DEBUG] Number of contours found: {len(contours)}")
    
    # Save all contours
    debug_all_contours = image.copy()
    cv2.drawContours(debug_all_contours, contours, -1, (0,255,0), 2)
    cv2.imwrite("step-by-step\\debug_07_all_contours.jpg", debug_all_contours)
    
    # Select the largest contour resembling a rectangle
    max_area = 0
    book_contour = None
    
    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area > 1000:  # Ignore small contours
            # Save each sufficiently large contour
            debug_contour = image.copy()
            cv2.drawContours(debug_contour, [cnt], -1, (0,255,0), 2)
            cv2.imwrite(f"step-by-step\\debug_08_contour_{i}.jpg", debug_contour)
            print(f"[DEBUG] Contour {i}: area = {area}")
            
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            print(f"[DEBUG] Contour {i}: number of points = {len(approx)}")
            
            if len(approx) == 4 and area > max_area:
                max_area = area
                book_contour = approx
                # Save the detected rectangle
                debug_rectangle = image.copy()
                cv2.drawContours(debug_rectangle, [approx], -1, (0,0,255), 3)
                cv2.imwrite(f"step-by-step\\debug_09_rectangle_{i}.jpg", debug_rectangle)
                print(f"[DEBUG] Rectangular contour {i} found")

    if book_contour is None:
        print("[DEBUG] No suitable rectangular contours found")
        raise Exception("Failed to find the book in the image")

    # Sort points for proper transformation
    pts = book_contour.reshape(4, 2)
    rect = np.zeros((4, 2), dtype=np.float32)
    
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # top-left
    rect[2] = pts[np.argmax(s)]  # bottom-right
    
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # top-right
    rect[3] = pts[np.argmax(diff)]  # bottom-left

    # Calculate output image dimensions
    width = max(
        int(np.linalg.norm(rect[1] - rect[0])),  # top
        int(np.linalg.norm(rect[2] - rect[3]))   # bottom
    )
    height = max(
        int(np.linalg.norm(rect[1] - rect[2])),  # right
        int(np.linalg.norm(rect[0] - rect[3]))   # left
    )

    # Target points for transformation
    dst = np.array([
        [0, 0],
        [width-1, 0],
        [width-1, height-1],
        [0, height-1]
    ], dtype=np.float32)

    # Apply perspective transformation
    matrix = cv2.getPerspectiveTransform(rect, dst)
    result = cv2.warpPerspective(original, matrix, (width, height))

    cv2.imwrite(output_path, result)
    print(f"Book image saved to {output_path}")

if __name__ == "__main__":
    try:
        input_path = 'cover4.jpg'
        output_path = 'step-by-step\\debug_00_without_cover.png'

        with open(input_path, 'rb') as i:
            with open(output_path, 'wb') as o:
                input = i.read()
                output = remove(input)
                o.write(output)
        find_book_cover("step-by-step\\debug_00_without_cover.png", "step-by-step\\debug_10_output.jpg")
    except Exception as e:
        print(f"Error: {e}")
