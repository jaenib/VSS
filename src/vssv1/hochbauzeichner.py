import cv2
import numpy as np

def get_outline(image, low_threshold=50, high_threshold=150):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # Convert to grayscale
    blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)  # Blur image to enhance edge detection
    edges = cv2.Canny(blurred_image, low_threshold, high_threshold)  # Use Canny Edge Detection to get edges

    # Invert the image
    #edges = cv2.bitwise_not(edges)
    
    return edges
