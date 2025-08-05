import cv2
import numpy as np
import easyocr
from difflib import SequenceMatcher
import os
import json
from datetime import datetime
import uuid
import winsound
import time

# Initialize EasyOCR reader once
print("Initializing EasyOCR reader...")
reader = easyocr.Reader(['en'])
print("EasyOCR reader initialized successfully!")

# Common Magic: The Gathering card names for reference/correction
COMMON_CARD_NAMES = [
    "Island", "Mountain", "Forest", "Plains", "Swamp",
    "Lightning Bolt", "Counterspell", "Giant Growth", "Dark Ritual",
    "Swords to Plowshares", "Path to Exile", "Brainstorm", "Ponder"
]

def fix_common_ocr_errors(text):
    """Fix common OCR misreadings"""
    if not text:
        return text
    
    corrections = {
        'Istaid': 'Island',
        'Isliid': 'Island', 
        'Usland': 'Island',
        'staid': 'sland',
        'slaid': 'sland',
        '1': 'I',
        '0': 'O'
    }
    
    corrected = text
    for wrong, right in corrections.items():
        corrected = corrected.replace(wrong, right)
    
    return corrected

def find_closest_card_name(detected_text, threshold=0.6):
    """Find the closest matching card name from common cards"""
    if not detected_text:
        return None
    
    best_match = None
    best_score = 0
    
    for card_name in COMMON_CARD_NAMES:
        similarity = SequenceMatcher(None, detected_text.lower(), card_name.lower()).ratio()
        
        if similarity > best_score and similarity >= threshold:
            best_score = similarity
            best_match = card_name
    
    if best_match:
        print(f"  🎯 Found close match: '{detected_text}' -> '{best_match}' (similarity: {best_score:.2%})")
        return best_match
    
    return None

def is_reasonable_text(text):
    """Check if text looks like a plausible word/name"""
    text = text.lower().strip()
    if len(text) < 2:
        return False
    
    vowels = {'a', 'e', 'i', 'o', 'u', 'y'}
    if len(text) > 4 and not any(vowel in text for vowel in vowels):
        return False
    
    return True

def find_text(frame, card_contour=None):
    try:
        # Use top portion of entire image
        h, w = frame.shape[:2]
        roi = frame[0:int(h*0.5), 0:w]  # Use top 50% for OCR
        
        if roi.size == 0:
            return None

        # Convert to grayscale
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Try multiple preprocessing methods
        processed_images = []
        
        _, thresh1 = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        processed_images.append(("Simple", thresh1))
        
        _, thresh2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(("Otsu", thresh2))
        
        thresh3 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        processed_images.append(("Adaptive", thresh3))
        
        processed_images.append(("Original", gray))

        all_results = []
        
        for method_name, img in processed_images:
            for scale_factor in [2, 3, 4]:
                scaled = cv2.resize(img, (0, 0), fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
                # result is a list of strings, e.g., ['Lightning', 'Bolt'] or ['Lightning Bolt']
                result_fragments = reader.readtext(scaled, detail=0)
                if result_fragments:
                    all_results.extend(result_fragments)

        # Process all results
        for text in all_results:
            if text and len(text) > 1:
                clean_text = ''.join(c for c in text if c.isalpha() or c.isspace()).strip()
                clean_text = ' '.join(clean_text.split())
                
                if clean_text:
                    corrected_text = fix_common_ocr_errors(clean_text)
                    
                    # Try to find close match first
                    close_match = find_closest_card_name(corrected_text)
                    if close_match:
                        return close_match
                    
                    # Otherwise validate as reasonable text
                    if len(corrected_text) >= 2 and is_reasonable_text(corrected_text):
                        return corrected_text.title()

        return None

    except Exception as e:
        print(f"OCR Error: {str(e)}")
        return None

def compare_strings(string1, string2):
    if not string1 or not string2:
        return 0.0
    
    string1 = str(string1).lower()
    string2 = str(string2).lower()
    
    matcher = SequenceMatcher(None, string1, string2)
    return matcher.ratio()

def save_card_to_products(card_data: dict) -> bool:
    """Save confirmed card data to products.json"""
    try:
        # Generate unique SKU
        timestamp = datetime.now().strftime('%Y%m%d')
        unique_id = str(uuid.uuid4())[:8]
        clean_name = ''.join(c for c in card_data['name'] if c.isalnum()).upper()
        sku = f"MTG-{clean_name}-{timestamp}-{unique_id}"
        
        product = {
            "sku": sku,
            "name": card_data['name'],
            "set_name": card_data.get('set_name', 'Unknown Set'),
            "rarity": card_data.get('rarity', 'Unknown'),
            "price": card_data.get('price', '1.00'),
            "image_url": card_data.get('card_url'),
            "oracle_text": card_data.get('oracle_text', ''),
            "flavor_text": card_data.get('flavor_text', ''),
            "collector_number": card_data.get('collector_number', '')
        }
        
        # Create new list with just the current product
        products = [product]
        
        # Save products (overwrites existing file)
        with open('products.json', 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
            
        print(f"✅ Successfully saved card to products.json with SKU: {sku}")
        print("🗑️ Previous listings were cleared")
        return True
        
    except Exception as e:
        print(f"❌ Error saving to products.json: {str(e)}")
        return False

def find_and_print_top_matches(detected_name, all_cards_data, top_n=6):
    """Finds and prints the top N card matches from the JSON data with user confirmation."""
    if not detected_name:
        return

    matches = []
    for card in all_cards_data:
        card_name = card.get('name')
        if card_name:
            similarity = compare_strings(detected_name, card_name)
            matches.append((similarity, card))

    # Sort by similarity, descending
    matches.sort(key=lambda x: x[0], reverse=True)

    # Print top N matches
    print(f"\n{'='*60}")
    print(f"TOP {top_n} MATCHES FOR '{detected_name.upper()}' IN THE DATABASE")
    print(f"{'='*60}")

    for i, (score, card) in enumerate(matches[:top_n]):
        print(f"\n[{i+1}] Match (Similarity: {score:.2%})")
        print(f"  Name:     {card.get('name', 'N/A')}")
        print(f"  Set:      {card.get('set_name', 'N/A')}")
        print(f"  Rarity:   {card.get('rarity', 'N/A')}")
        print(f"  Price:    ${card.get('price', 'N/A')}")
        print(f"  Card URL: {card.get('card_url', 'N/A')}")
    
    print("\nIs one of these matches correct?")
    print("Enter the number of the correct match (1-8), or:")
    print("'n' for none of these")
    print("'s' to skip saving")
    print("'f' to filter by set name")
    
    while True:
        choice = input("\nYour choice: ").strip().lower()
        
        if choice == 'n':
            print("❌ No correct match found.")
            return
        elif choice == 's':
            print("⏭️ Skipping save operation.")
            return
        elif choice == 'f':
            # Filter by set name
            set_filter = input("Enter set name to filter by (e.g., 'Core Set 2021', 'Dominaria'): ").strip()
            if set_filter:
                filtered_matches = []
                for score, card in matches:
                    card_set = card.get('set_name', '').lower()
                    if set_filter.lower() in card_set:
                        filtered_matches.append((score, card))
                
                if filtered_matches:
                    print(f"\n{'='*60}")
                    print(f"FILTERED MATCHES FOR '{detected_name.upper()}' IN SET '{set_filter.upper()}'")
                    print(f"{'='*60}")
                    
                    for i, (score, card) in enumerate(filtered_matches[:top_n]):
                        print(f"\n[{i+1}] Match (Similarity: {score:.2%})")
                        print(f"  Name:     {card.get('name', 'N/A')}")
                        print(f"  Set:      {card.get('set_name', 'N/A')}")
                        print(f"  Rarity:   {card.get('rarity', 'N/A')}")
                        print(f"  Price:    ${card.get('price', 'N/A')}")
                        print(f"  Card URL: {card.get('card_url', 'N/A')}")
                    
                    print(f"\nEnter the number of the correct match (1-{min(len(filtered_matches), top_n)}), or:")
                    print("'b' to go back to all matches")
                    print("'n' for none of these")
                    print("'s' to skip saving")
                    
                    while True:
                        filter_choice = input("\nYour choice: ").strip().lower()
                        if filter_choice == 'b':
                            break
                        elif filter_choice == 'n':
                            print("❌ No correct match found.")
                            return
                        elif filter_choice == 's':
                            print("⏭️ Skipping save operation.")
                            return
                        elif filter_choice.isdigit() and 1 <= int(filter_choice) <= min(len(filtered_matches), top_n):
                            selected_card = filtered_matches[int(filter_choice)-1][1]
                            # Confirm price
                            current_price = selected_card.get('price', '1.00')
                            print(f"\nCurrent price: ${current_price}")
                            new_price = input("Enter new price (press Enter to keep current): ").strip()
                            
                            if new_price and new_price.replace('.', '').isdigit():
                                selected_card['price'] = new_price
                            
                            # Save to products.json
                            if save_card_to_products(selected_card):
                                print("✨ Card successfully added to inventory!")
                            return
                        else:
                            print("❌ Invalid choice. Please try again.")
                else:
                    print(f"❌ No matches found in set '{set_filter}'")
                    print("Showing all matches again...")
                    break
            else:
                print("❌ No set name entered. Showing all matches...")
                break
        elif choice.isdigit() and 1 <= int(choice) <= min(top_n, len(matches)):
            # Get the selected card
            selected_card = matches[int(choice)-1][1]
            
            # Confirm price
            current_price = selected_card.get('price', '1.00')
            print(f"\nCurrent price: ${current_price}")
            new_price = input("Enter new price (press Enter to keep current): ").strip()
            
            if new_price and new_price.replace('.', '').isdigit():
                selected_card['price'] = new_price
            
            # Save to products.json
            if save_card_to_products(selected_card):
                print("✨ Card successfully added to inventory!")
            return
        else:
            print("❌ Invalid choice. Please try again.")

def is_card_aligned(roi, debug_out=None):
    """Check if a card is likely aligned in the ROI using variance and edge/contour detection (more permissive, with debug)."""
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    variance = np.var(gray)
    sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
    if variance < 80:  # Slightly lowered
        if debug_out is not None:
            debug_out['variance'] = variance
            debug_out['sharpness'] = sharpness
            debug_out['contours'] = 0
            debug_out['max_area'] = 0
        return False
    edges = cv2.Canny(gray, 40, 120)  # Slightly lowered
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    max_area = 0
    card_like = False
    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, 0.06 * cv2.arcLength(cnt, True), True)  # More deviation allowed
        area = cv2.contourArea(cnt)
        if area > max_area:
            max_area = area
        if 4 <= len(approx) <= 8 and area > 0.05 * roi.shape[0] * roi.shape[1]:  # Lowered area, more points
            card_like = True
    if debug_out is not None:
        debug_out['variance'] = variance
        debug_out['sharpness'] = sharpness
        debug_out['contours'] = len(contours)
        debug_out['max_area'] = max_area
    return card_like

def is_sharp(roi, threshold=100):
    """Check if the ROI is sharp enough using Laplacian variance."""
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return lap_var > threshold

def is_bbox_inside_border(bbox, border_rect, margin=0):
    """Check if the bounding box is mostly inside the border rectangle."""
    x, y, w, h = bbox
    bx, by, bw, bh = border_rect
    return (
        x + margin > bx and y + margin > by and
        x + w - margin < bx + bw and y + h - margin < by + bh
    )

def is_bbox_fully_inside_border(bbox, border_rect, margin=0):
    """Check if the entire bounding box is fully inside the border rectangle (strict)."""
    x, y, w, h = bbox
    bx, by, bw, bh = border_rect
    return (
        x + margin >= bx and y + margin >= by and
        x + w - margin <= bx + bw and y + h - margin <= by + bh
    )

def is_bbox_similar(bbox1, bbox2, pos_thresh=10, size_thresh=10):
    """Check if two bounding boxes are similar in position and size (for stillness detection)."""
    if bbox1 is None or bbox2 is None:
        return False
    x1, y1, w1, h1 = bbox1
    x2, y2, w2, h2 = bbox2
    return (
        abs(x1 - x2) < pos_thresh and
        abs(y1 - y2) < pos_thresh and
        abs(w1 - w2) < size_thresh and
        abs(h1 - h2) < size_thresh
    )

def detect_card_quads(frame, area_lower=0.15, area_upper=0.35, aspect_low=0.65, aspect_high=0.78):
    """
    Enhanced card detection using multiple preprocessing techniques and robust contour analysis.
    Incorporates techniques from carddtest3.py and carddetectorexample.py for better detection.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame_area = frame.shape[0] * frame.shape[1]
    card_candidates = []
    
    # Try multiple preprocessing approaches for robustness
    preprocessing_methods = []
    
    # Method 1: Adaptive thresholding (from carddtest3.py)
    blur_radius = max(3, min(frame.shape[:2]) // 100)
    if blur_radius % 2 == 0:
        blur_radius += 1
    img_blur = cv2.medianBlur(gray, blur_radius)
    thresh_adaptive = cv2.adaptiveThreshold(img_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                          cv2.THRESH_BINARY_INV, 11, 5)
    preprocessing_methods.append(thresh_adaptive)
    
    # Method 2: Simple thresholding (from carddetectorexample.py)
    _, thresh_simple = cv2.threshold(gray, 100, 255, 0)
    preprocessing_methods.append(thresh_simple)
    
    # Method 3: Otsu thresholding
    _, thresh_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    preprocessing_methods.append(thresh_otsu)
    
    for method_idx, thresh_img in enumerate(preprocessing_methods):
        # Apply morphological operations to clean up the image
        kernel_size = max(3, min(frame.shape[:2]) // 200)
        if kernel_size % 2 == 0:
            kernel_size += 1
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        
        # Dilate then erode to remove noise and connect card edges
        img_dilate = cv2.dilate(thresh_img, kernel, iterations=1)
        img_erode = cv2.erode(img_dilate, kernel, iterations=1)
        
        # Find contours with hierarchy
        contours, hierarchy = cv2.findContours(img_erode, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) == 0:
            continue
            
        # Analyze contours with hierarchy (from carddtest3.py)
        stack = [(0, hierarchy[0][0])]
        while len(stack) > 0:
            i_cnt, h = stack.pop()
            i_next, i_prev, i_child, i_parent = h
            
            if i_next != -1:
                stack.append((i_next, hierarchy[0][i_next]))
                
            cnt = contours[i_cnt]
            area = cv2.contourArea(cnt)
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
            
            # Check if contour is rectangular and meets size criteria
            if len(approx) == 4 and area >= frame_area * area_lower and area <= frame_area * area_upper:
                # Get the minimum area rectangle
                rect = cv2.minAreaRect(cnt)
                (x, y), (width, height), angle = rect
                
                # Check aspect ratio
                aspect = min(width, height) / max(width, height)
                if aspect_low <= aspect <= aspect_high:
                    # Additional validation: check edge density and color variance
                    box = cv2.boxPoints(rect)
                    box = box.astype(int)
                    
                    # Create a mask for this contour
                    mask = np.zeros(gray.shape, dtype=np.uint8)
                    cv2.drawContours(mask, [cnt], -1, 255, -1)
                    
                    # Check edge density within the contour
                    edges = cv2.Canny(gray, 50, 150)
                    edge_density = np.sum(edges & mask) / np.sum(mask)
                    
                    # Cards should have moderate edge density
                    if 0.01 <= edge_density <= 0.3:
                        # Color variance validation
                        x, y, w, h = cv2.boundingRect(cnt)
                        roi = frame[y:y+h, x:x+w]
                        
                        # Create a mask for the contour within the ROI
                        roi_mask = np.zeros((h, w), dtype=np.uint8)
                        contour_in_roi = cnt - np.array([x, y])
                        cv2.drawContours(roi_mask, [contour_in_roi], -1, 255, -1)
                        
                        # Calculate color variance within the contour
                        if np.sum(roi_mask) > 0:
                            mask_indices = roi_mask > 0
                            if np.sum(mask_indices) > 100:
                                roi_colors = roi[mask_indices]
                                color_variance = np.var(roi_colors, axis=0)
                                total_variance = np.sum(color_variance)
                                
                                # Reject if color variance is too low (uniform color)
                                if total_variance >= 500:
                                    card_candidates.append(box)
                                    # Don't break - continue finding all cards in this method
            
            # Check child contours
            if i_child != -1:
                stack.append((i_child, hierarchy[0][i_child]))
    
    return card_candidates

def perspective_transform_from_box(frame, box):
    """
    Enhanced perspective transform with better point ordering and error handling.
    Incorporates techniques from carddetectorexample.py for robust transformation.
    """
    try:
        # Order points: top-left, top-right, bottom-right, bottom-left
        pts = box.astype("float32")
        
        # Calculate the sum and difference of coordinates to determine corner order
        s = pts.sum(axis=1)
        diff = np.diff(pts, axis=1)
        
        rect = np.zeros((4, 2), dtype="float32")
        rect[0] = pts[np.argmin(s)]  # top-left
        rect[2] = pts[np.argmax(s)]  # bottom-right
        rect[1] = pts[np.argmin(diff)]  # top-right
        rect[3] = pts[np.argmax(diff)]  # bottom-left
        
        # Calculate the width and height of the new image
        widthA = np.linalg.norm(rect[2] - rect[3])
        widthB = np.linalg.norm(rect[1] - rect[0])
        maxWidth = int(max(widthA, widthB))
        
        heightA = np.linalg.norm(rect[1] - rect[2])
        heightB = np.linalg.norm(rect[0] - rect[3])
        maxHeight = int(max(heightA, heightB))
        
        # Ensure minimum dimensions
        maxWidth = max(maxWidth, 50)
        maxHeight = max(maxHeight, 70)
        
        # Define the destination points for the perspective transform
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ], dtype="float32")
        
        # Calculate the perspective transform matrix
        M = cv2.getPerspectiveTransform(rect, dst)
        
        # Apply the perspective transform
        warped = cv2.warpPerspective(frame, M, (maxWidth, maxHeight))
        
        return warped
        
    except Exception as e:
        print(f"Perspective transform error: {str(e)}")
        return None

def extract_name_box(card_img):
    """Crop the top portion of the card image for the name box with better precision."""
    h, w = card_img.shape[:2]
    # Magic cards typically have the name in the top 15-20% of the card
    # Use a slightly larger region to ensure we capture the full name
    name_box = card_img[0:int(h*0.20), 0:w]
    return name_box

def visualize_card_detections(frame, card_quads, detected_names):
    """Create a debug visualization showing detected card regions and their names."""
    debug_frame = frame.copy()
    
    for idx, box in enumerate(card_quads):
        # Draw the card contour
        cv2.drawContours(debug_frame, [box], -1, (0, 255, 0), 2)
        
        # Get bounding box
        x, y, w, h = cv2.boundingRect(box)
        
        # Draw bounding rectangle
        cv2.rectangle(debug_frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        
        # Add card number label
        cv2.putText(debug_frame, f"Card {idx+1}", (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Add detected name if available
        if idx < len(detected_names):
            cv2.putText(debug_frame, detected_names[idx], (x, y+h+20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    return debug_frame

# Improved preprocessing for OCR
def preprocess_for_ocr(img):
    """Try several preprocessing methods and return the best result for OCR."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    results = []
    # Simple threshold
    _, thresh1 = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    results.append(thresh1)
    # Otsu threshold
    _, thresh2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    results.append(thresh2)
    # Adaptive threshold
    thresh3 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    results.append(thresh3)
    # Original gray
    results.append(gray)
    return results

def is_uniform_color(roi, variance_thresh=300):
    """Return True if the ROI is nearly a single color (low variance)."""
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    var = np.var(gray)
    return var < variance_thresh

def is_green_dominant(roi, green_thresh=150):
    """Return True if the ROI is mostly green."""
    mean_color = cv2.mean(roi)
    # mean_color = (B, G, R, alpha)
    return mean_color[1] > green_thresh and mean_color[1] > mean_color[0] and mean_color[1] > mean_color[2]

def edge_density(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    return np.sum(edges > 0) / edges.size

def black_white_ratio(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, bw = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    black = np.sum(bw == 0)
    white = np.sum(bw == 255)
    total = bw.size
    return black / total, white / total

def mean_brightness(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    return np.mean(gray)



def webcam_mode(cam_index=1):
    """
    Enhanced webcam mode with improved card detection and video processing.
    Incorporates techniques from analyzed scripts for better performance.
    """
    print(f"\nInitializing camera {cam_index}...")
    
    # Use the camera index the user specified
    print(f"\n📷 Using camera index {cam_index}")
    backends = [
        (cv2.CAP_DSHOW, "DirectShow"),
        (cv2.CAP_ANY, "Auto"),
        (cv2.CAP_MSMF, "Media Foundation"),
        (cv2.CAP_FFMPEG, "FFMPEG")
    ]
    
    backend = None
    backend_name = "Unknown"
    
    for b, name in backends:
        print(f"Trying {name} backend...")
        cap = cv2.VideoCapture(cam_index, b)
        
        if cap.isOpened():
            # Test if we can actually read frames
            ret, test_frame = cap.read()
            if ret and test_frame is not None:
                backend = b
                backend_name = name
                print(f"✅ Camera {cam_index} initialized successfully with {name} backend!")
                break
            else:
                print(f"❌ Camera {cam_index} opened with {name} but could not read frames")
                cap.release()
        else:
            print(f"❌ Could not open camera {cam_index} with {name} backend")
            cap.release()
    
    if backend is None:
        print("❌ Could not open webcam with any backend.")
        print("Try running option 5 (Test camera connection) to diagnose the issue.")
        return
    
    # Create camera capture with the working backend
    cap = cv2.VideoCapture(cam_index, backend)
    
    # Set optimal camera parameters
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Higher resolution for better detection
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Enable auto exposure
    
    # Wait for camera to initialize
    print("Waiting for camera to stabilize...")
    for attempt in range(10):
        ret, test_frame = cap.read()
        if ret and test_frame is not None:
            print("✅ Camera stabilized successfully!")
            break
        time.sleep(0.5)
    else:
        print("❌ Error: Could not read from camera after initialization attempts")
        cap.release()
        return

    # Wait for camera to stabilize
    time.sleep(1.0)

    # --- Auto-detect frame size from first frame ---
    ret, frame = cap.read()
    if not ret or frame is None:
        print("❌ Could not read initial frame for resolution detection.")
        cap.release()
        return
    frame_h, frame_w = frame.shape[:2]
    print(f"Detected camera resolution: {frame_w}x{frame_h}")

    # Border setup (now dynamic)
    border_color = (255, 255, 255)
    border_thickness = 3
    card_height = int(frame_h * 0.6)
    card_width = int(card_height * (63 / 88))
    bx = (frame_w - card_width) // 2
    by = (frame_h - card_height) // 2
    border_rect = (bx, by, card_width, card_height)

    # Frame buffer for improved detection
    frame_buffer = []
    buffer_size = 3

    while True:
        try:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("Warning: Could not read frame from camera")
                continue

            # --- Dynamically update frame size and border if resolution changes ---
            if frame.shape[0] != frame_h or frame.shape[1] != frame_w:
                frame_h, frame_w = frame.shape[:2]
                print(f"Resolution changed: {frame_w}x{frame_h}")
                card_height = int(frame_h * 0.6)
                card_width = int(card_height * (63 / 88))
                bx = (frame_w - card_width) // 2
                by = (frame_h - card_height) // 2
                border_rect = (bx, by, card_width, card_height)
            
            # Draw border
            cv2.rectangle(frame, (bx, by), (bx + card_width, by + card_height), border_color, border_thickness)
            
            # Rotate if portrait
            if frame.shape[0] > frame.shape[1]:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            
            # Enhanced detection logic
            best_box = None
            if current_time - last_detection_time >= detection_interval:
                # Use middle frame from buffer for detection
                detection_frame = frame_buffer[len(frame_buffer) // 2] if frame_buffer else frame
                
                # Detect cards using improved algorithm
                card_quads = detect_card_quads(detection_frame)
                
                # Find the best card within border
                for box in card_quads:
                    x, y, w, h = cv2.boundingRect(box)
                    if is_bbox_fully_inside_border((x, y, w, h), border_rect, margin=10):
                        best_box = box
                        break
                
                last_detection_time = current_time
            
            # Process detected card
            if best_box is not None:
                try:
                    # Draw detection visualization
                    cv2.drawContours(frame, [best_box], 0, (0, 255, 0), 2)
                    x, y, w, h = cv2.boundingRect(best_box)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    
                    # Show card preview
                    warped_card = perspective_transform_from_box(frame, best_box)
                    if warped_card is not None:
                        preview_h, preview_w = 100, 70
                        preview = cv2.resize(warped_card, (preview_w, preview_h))
                        if 10 + preview_h < frame.shape[0] and 10 + preview_w < frame.shape[1]:
                            frame[10:10+preview_h, 10:10+preview_w] = preview
                            cv2.rectangle(frame, (10, 10), (10+preview_w, 10+preview_h), (255, 0, 0), 2)
                    
                    # Perform OCR on detected card
                    if warped_card is not None:
                        name_box = extract_name_box(warped_card)
                        detected_name = find_text(name_box)
                        
                        if detected_name and len(detected_name) >= 4:
                            # Check debounce
                            if (not last_detected or 
                                detected_name != last_detected or 
                                current_time - last_detected_time > debounce_seconds):
                                
                                detected_cards.append({
                                    'name': detected_name,
                                    'timestamp': current_time
                                })
                                last_detected = detected_name
                                last_detected_time = current_time
                                
                                # Visual feedback
                                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 4)
                                cv2.putText(frame, f"Detected: {detected_name}", 
                                          (x, y - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                                
                                # Audio feedback
                                try:
                                    winsound.MessageBeep()
                                except Exception:
                                    pass
                                
                                print(f"🎯 Detected card: {detected_name}")
                    
                    cv2.putText(frame, "Card detected - processing", (x, y - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                except Exception as e:
                    print(f"Error processing detected card: {e}")
            else:
                cv2.putText(frame, "No card detected in border", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Display status
            status = f"Detection interval: {detection_interval}s | Cards detected: {len(detected_cards)}"
            cv2.putText(frame, status, (10, frame.shape[0] - 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, "Press 'q' to finish", (10, frame.shape[0] - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow('Enhanced Card Detection (Webcam)', frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
        except Exception as e:
            print(f"Error in webcam loop: {e}")
            continue
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"\nSession ended. {len(detected_cards)} card(s) detected.")
    if not detected_cards:
        print("No cards detected.")
        return
    
    # Process detected cards
    unique_cards = []
    seen = set()
    for card in detected_cards:
        if card['name'] not in seen:
            unique_cards.append(card)
            seen.add(card['name'])
    
    try:
        json_path = os.path.join(os.path.dirname(__file__), 'mtg_cards_data.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            all_cards_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: 'mtg_cards_data.json' not found in the script directory.")
        return
    except json.JSONDecodeError:
        print("❌ Error: Could not decode 'mtg_cards_data.json'. Please check if it's a valid JSON file.")
        return
    
    for card in unique_cards:
        print(f"\n{'='*60}")
        print(f"Verifying detected card: {card['name']}")
        print(f"{'='*60}")
        find_and_print_top_matches(card['name'], all_cards_data)
    
    print("\nAll detected cards processed.")

def test_card_detection_mode(cam_index=1):
    """Enhanced test mode to visualize card detection without OCR processing."""
    print(f"\nStarting enhanced test mode (camera index {cam_index}). Press 'q' to exit.")
    print("This mode shows improved card detection visualization without OCR processing.")
    
    # Try different camera backends
    backends = [
        (cv2.CAP_DSHOW, "DirectShow"),
        (cv2.CAP_ANY, "Auto"),
        (cv2.CAP_MSMF, "Media Foundation"),
        (cv2.CAP_FFMPEG, "FFMPEG")
    ]
    
    cap = None
    backend_name = "Unknown"
    
    for backend, name in backends:
        print(f"Trying {name} backend...")
        cap = cv2.VideoCapture(cam_index, backend)
        
        if cap.isOpened():
            # Test if we can actually read frames
            ret, test_frame = cap.read()
            if ret and test_frame is not None:
                backend_name = name
                print(f"✅ Camera {cam_index} initialized successfully with {name} backend!")
                break
            else:
                print(f"❌ Camera {cam_index} opened with {name} but could not read frames")
                cap.release()
        else:
            print(f"❌ Could not open camera {cam_index} with {name} backend")
            cap.release()
    
    if cap is None or not cap.isOpened():
        print("❌ Could not open webcam with any backend.")
        print("Try running option 5 (Test camera connection) to diagnose the issue.")
        return

    # Set optimal camera parameters
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)

    # Border setup
    border_color = (255, 255, 255)
    border_thickness = 3
    frame_h, frame_w = 480, 640
    card_height = int(frame_h * 0.6)
    card_width = int(card_height * (63 / 88))
    bx = (frame_w - card_width) // 2
    by = (frame_h - card_height) // 2
    border_rect = (bx, by, card_width, card_height)

    # Detection statistics
    detection_count = 0
    total_frames = 0
    detection_interval = 0.2  # Detection every 0.2 seconds for testing
    last_detection_time = 0

    while True:
        try:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("Warning: Could not read frame from camera")
                continue
                
            current_time = time.time()
            total_frames += 1
            
            # Adjust border for current frame size
            if frame.shape[0] != frame_h or frame.shape[1] != frame_w:
                frame_h, frame_w = frame.shape[:2]
                card_height = int(frame_h * 0.6)
                card_width = int(card_height * (63 / 88))
                bx = (frame_w - card_width) // 2
                by = (frame_h - card_height) // 2
                border_rect = (bx, by, card_width, card_height)
            
            # Draw border
            cv2.rectangle(frame, (bx, by), (bx + card_width, by + card_height), border_color, border_thickness)
            
            # Rotate if portrait
            if frame.shape[0] > frame.shape[1]:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            
            # Run detection at intervals
            card_contours = []
            if current_time - last_detection_time >= detection_interval:
                # Detect card contours using improved algorithm
                card_contours = detect_card_quads(frame)
                last_detection_time = current_time
                
                # Draw all detected contours
                for i, card in enumerate(card_contours):
                    try:
                        # Draw contour
                        cv2.drawContours(frame, [card], -1, (0, 255, 0), 2)
                        
                        # Draw bounding box
                        x, y, w, h = cv2.boundingRect(card)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                        
                        # Check if card is inside border
                        in_border = is_bbox_fully_inside_border((x, y, w, h), border_rect, margin=10)
                        border_color_detection = (0, 255, 255) if in_border else (0, 0, 255)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), border_color_detection, 3)
                        
                        # Show card info
                        area = w * h
                        aspect = w / h if h > 0 else 0
                        cv2.putText(frame, f"Card {i+1}: Area={area:.0f}, Aspect={aspect:.2f}", 
                                   (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                        
                        # Show border status
                        border_status = "IN BORDER" if in_border else "OUTSIDE BORDER"
                        cv2.putText(frame, border_status, (x, y + h + 20), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, border_color_detection, 2)
                        
                        # Try perspective transform
                        warped = perspective_transform_from_box(frame, card)
                        if warped is not None:
                            # Show warped preview
                            preview_h, preview_w = 80, 55
                            preview = cv2.resize(warped, (preview_w, preview_h))
                            preview_y = 10 + i * (preview_h + 5)
                            if preview_y + preview_h < frame.shape[0]:
                                frame[preview_y:preview_y+preview_h, 10:10+preview_w] = preview
                                cv2.rectangle(frame, (10, preview_y), (10+preview_w, preview_y+preview_h), (0, 255, 255), 2)
                        
                        detection_count += 1
                    except Exception as e:
                        print(f"Error processing card contour: {e}")
                        continue
            
            # Show statistics
            fps = total_frames / (current_time - time.time() + 1) if total_frames > 0 else 0
            detection_rate = detection_count / total_frames if total_frames > 0 else 0
            
            cv2.putText(frame, f"FPS: {fps:.1f} | Detection Rate: {detection_rate:.2%}", 
                       (10, frame.shape[0] - 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Cards detected: {len(card_contours)}", 
                       (10, frame.shape[0] - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, "Press 'q' to exit test mode", (10, frame.shape[0] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow('Enhanced Card Detection Test Mode', frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
        except Exception as e:
            print(f"Error in test mode loop: {e}")
            continue
    
    cap.release()
    cv2.destroyAllWindows()
    print(f"Test mode ended. Processed {total_frames} frames, detected {detection_count} cards.")

def show_obs_setup_instructions():
    """Show detailed OBS setup instructions."""
    print("\n" + "="*60)
    print("📋 OBS STUDIO SETUP INSTRUCTIONS")
    print("="*60)
    print("\n1. 📥 INSTALL OBS STUDIO:")
    print("   - Download from: https://obsproject.com/")
    print("   - Install with default settings")
    print("   - Restart your computer after installation")
    
    print("\n2. 🎥 ADD YOUR WINDOWS LINK CAMERA:")
    print("   - Open OBS Studio")
    print("   - In Sources panel, click '+' → 'Video Capture Device'")
    print("   - Name it 'Windows Link Camera'")
    print("   - In Device dropdown, select your Windows Link camera")
    print("   - Set Resolution to '1280x720' or '1920x1080'")
    print("   - Click 'OK'")
    
    print("\n3. 🎬 START VIRTUAL CAMERA:")
    print("   - Go to Tools → Start Virtual Camera")
    print("   - You should see 'Virtual Camera Active' in status bar")
    print("   - Keep OBS running in background")
    
    print("\n4. 🧪 TEST THE SETUP:")
    print("   - Run this script")
    print("   - Choose option 7 (Detect OBS Virtual Camera)")
    print("   - If detected, choose option 2 (Webcam live mode)")
    
    print("\n5. 🔧 TROUBLESHOOTING:")
    print("   - If Virtual Camera doesn't start: Restart OBS")
    print("   - If camera not detected: Check Windows Camera app first")
    print("   - If poor quality: Adjust OBS canvas resolution")
    print("   - If laggy: Reduce OBS output resolution")
    
    print("\n6. ⚡ OPTIMIZATION TIPS:")
    print("   - Use 1280x720 resolution for best performance")
    print("   - Close other camera apps while using OBS")
    print("   - Keep OBS canvas and output resolutions the same")
    print("   - Use 'Start Virtual Camera' before running this script")
    
    print("\n" + "="*60)

def detect_obs_virtual_camera():
    """Detect OBS Virtual Camera specifically."""
    print("\n🔍 Detecting OBS Virtual Camera...")
    
    # OBS Virtual Camera typically appears at specific indices
    obs_indices = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    
    # Try different backends that work well with OBS
    backends = [
        (cv2.CAP_DSHOW, "DirectShow"),
        (cv2.CAP_ANY, "Auto"),
        (cv2.CAP_MSMF, "Media Foundation")
    ]
    
    for cam_index in obs_indices:
        for backend, name in backends:
            cap = cv2.VideoCapture(cam_index, backend)
            
            if cap.isOpened():
                # Try to read a frame
                ret, frame = cap.read()
                if ret and frame is not None:
                    # Check if this looks like OBS Virtual Camera
                    # OBS typically outputs at specific resolutions
                    height, width = frame.shape[:2]
                    
                    # Common OBS resolutions
                    obs_resolutions = [
                        (1920, 1080), (1280, 720), (854, 480), 
                        (640, 480), (1280, 960), (1600, 900)
                    ]
                    
                    is_obs_likely = (width, height) in obs_resolutions
                    
                    print(f"✅ Found camera at index {cam_index} with {name} backend")
                    print(f"   Resolution: {width}x{height}")
                    print(f"   Likely OBS Virtual Camera: {'Yes' if is_obs_likely else 'Maybe'}")
                    
                    cap.release()
                    return cam_index, backend, name, (width, height)
                cap.release()
    
    print("❌ OBS Virtual Camera not detected")
    print("\n📋 OBS Setup Instructions:")
    print("1. Open OBS Studio")
    print("2. Add your Windows Link camera as a source")
    print("3. Go to Tools → Start Virtual Camera")
    print("4. Run this script again")
    
    return None, None, None, None

def optimize_for_obs_virtual_camera(cap):
    """Optimize camera settings for OBS Virtual Camera."""
    print("🔧 Optimizing for OBS Virtual Camera...")
    
    # OBS Virtual Camera works best with these settings
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # Disable autofocus for virtual camera
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for lower latency
    
    print("✅ OBS Virtual Camera optimization applied")

def test_camera_simple(cam_index=1):
    """Simple camera test to check if camera is working properly."""
    print(f"\nTesting camera {cam_index}...")
    
    # Try different camera backends
    backends = [
        (cv2.CAP_DSHOW, "DirectShow"),
        (cv2.CAP_ANY, "Auto"),
        (cv2.CAP_MSMF, "Media Foundation"),
        (cv2.CAP_FFMPEG, "FFMPEG")
    ]
    
    for backend, name in backends:
        print(f"Trying {name} backend...")
        cap = cv2.VideoCapture(cam_index, backend)
        
        if cap.isOpened():
            # Try to read a few frames
            for i in range(5):
                ret, frame = cap.read()
                if ret and frame is not None:
                    print(f"✅ Camera {cam_index} is working with {name} backend! Frame size: {frame.shape}")
                    cap.release()
                    return True
                time.sleep(0.5)
            
            print(f"❌ Camera {cam_index} opened with {name} but could not read frames")
            cap.release()
        else:
            print(f"❌ Could not open camera {cam_index} with {name} backend")
    
    print(f"❌ Camera {cam_index} failed with all backends")
    return False

def find_available_cameras(max_index=10):
    """Find all available cameras and their working backends."""
    print(f"\nScanning for available cameras (0 to {max_index})...")
    available_cameras = []
    
    for cam_index in range(max_index + 1):
        print(f"\nTesting camera index {cam_index}...")
        
        # Try different camera backends
        backends = [
            (cv2.CAP_DSHOW, "DirectShow"),
            (cv2.CAP_ANY, "Auto"),
            (cv2.CAP_MSMF, "Media Foundation"),
            (cv2.CAP_FFMPEG, "FFMPEG")
        ]
        
        working_backends = []
        
        for backend, name in backends:
            cap = cv2.VideoCapture(cam_index, backend)
            
            if cap.isOpened():
                # Test if we can actually read frames
                ret, test_frame = cap.read()
                if ret and test_frame is not None:
                    working_backends.append(name)
                    print(f"  ✅ {name} backend works")
                else:
                    print(f"  ❌ {name} backend opened but no frames")
                cap.release()
            else:
                print(f"  ❌ {name} backend failed")
        
        if working_backends:
            available_cameras.append((cam_index, working_backends))
            print(f"✅ Camera {cam_index} is available with backends: {', '.join(working_backends)}")
        else:
            print(f"❌ Camera {cam_index} is not available")
    
    if available_cameras:
        print(f"\n🎉 Found {len(available_cameras)} available camera(s):")
        for cam_index, backends in available_cameras:
            print(f"  Camera {cam_index}: {', '.join(backends)}")
    else:
        print("\n❌ No cameras found. Please check your camera connections.")
    
    return available_cameras

def preview_all_cameras(max_index=4):
    print("\nTesting camera indexes 0 to", max_index)
    for idx in range(max_index + 1):
        print(f"Trying camera index {idx}...")
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                cv2.imshow(f'Camera {idx}', frame)
                print(f"Camera {idx} opened. Press any key to close preview.")
                cv2.waitKey(0)
                cv2.destroyAllWindows()
            else:
                print(f"Camera {idx} opened but no frame received.")
            cap.release()
        else:
            print(f"Camera {idx} could not be opened.")

def main():
    """Main function to run the card name detection"""
    while True:
        print("\nChoose mode:")
        print("1. Image file mode (type '1')")
        print("2. Webcam live mode (type '2')")
        print("3. Test card detection mode (type '3')")
        print("4. Preview all camera indexes (type '4')")
        print("5. Test camera connection (type '5')")
        print("6. Scan for available cameras (type '6')")
        print("7. Detect OBS Virtual Camera (type '7')")
        print("8. Show OBS Setup Instructions (type '8')")
        print("Type 'quit' or 'exit' to quit the program.")
        print("-" * 60)
        mode = input("Enter mode: ").strip().lower()
        if mode in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        elif mode == '1':
            print("\nPlease enter the path to your card image.")
            print("Examples:")
            print("  - C:/Users/dakot/OneDrive/Desktop/card.jpg")
            print("  - ./images/magic_card.png")
            print("  - card_image.jpg")
            print("\nType 'quit' or 'exit' to quit the program.")
            print("-" * 60)
            image_path = input("Enter image path: ").strip()
            if image_path.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            image_path = image_path.strip('"').strip("'")
            if not image_path:
                print("❌ Please enter a valid path.")
                continue
            if not os.path.exists(image_path):
                print(f"❌ File not found: '{image_path}'")
                continue
            print(f"\n📅 Processing started...")
            print(f"🎯 PROCESSING IMAGE: {os.path.basename(image_path)}")
            frame = cv2.imread(image_path)
            if frame is None:
                print(f"❌ Error: Could not load image '{image_path}'")
                continue
            print(f"✅ Image loaded successfully!")
            print(f"📏 Image dimensions: {frame.shape[1]}x{frame.shape[0]} pixels")

            # --- MULTI-CARD DETECTION LOGIC ---
            card_quads = detect_card_quads(frame, area_lower=0.03, area_upper=0.4, aspect_low=0.6, aspect_high=0.8)
            print(f"[DEBUG] Detected {len(card_quads)} card-like regions in the image.")
            detected_names = []
            
            for idx, box in enumerate(card_quads):
                # Get bounding box coordinates for debugging
                x, y, w, h = cv2.boundingRect(box)
                print(f"[DEBUG] Processing card region {idx+1}/{len(card_quads)} at ({x},{y}) size {w}x{h}")
                
                warped_card = perspective_transform_from_box(frame, box)
                if warped_card is not None:
                    # Extract name box from the top portion of the card
                    name_box = extract_name_box(warped_card)
                    print(f"[DEBUG] Card {idx+1} name box extracted: {name_box.shape[1]}x{name_box.shape[0]} pixels")
                    
                    # --- Enhanced preprocessing for OCR ---
                    # 1. Sharpen
                    kernel_sharpen = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
                    sharpened = cv2.filter2D(name_box, -1, kernel_sharpen)
                    # 2. Contrast enhancement
                    lab = cv2.cvtColor(sharpened, cv2.COLOR_BGR2LAB)
                    l, a, b = cv2.split(lab)
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                    cl = clahe.apply(l)
                    limg = cv2.merge((cl,a,b))
                    contrast = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
                    # 3. Denoise
                    denoised = cv2.fastNlMeansDenoisingColored(contrast, None, 10, 10, 7, 21)
                    # Try all thresholding methods
                    gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)
                    _, thresh1 = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
                    _, thresh2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    thresh3 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
                    ocr_images = [gray, thresh1, thresh2, thresh3]
                    best_text = ''
                    best_alpha_count = 0
                    for i, ocr_img in enumerate(ocr_images):
                        # Use EasyOCR with allowlist for A-Z, a-z, and space
                        result_fragments = reader.readtext(ocr_img, detail=0, allowlist='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ')
                        for text in result_fragments:
                            clean_text = ''.join(c for c in text if c.isalpha() or c.isspace()).strip()
                            alpha_count = sum(1 for c in clean_text if c.isalpha())
                            if alpha_count > best_alpha_count:
                                best_text = clean_text
                                best_alpha_count = alpha_count
                    print(f"[DEBUG] Card {idx+1} OCR result: '{best_text}' (alpha count: {best_alpha_count})")
                    if best_text and best_text not in detected_names:
                        detected_names.append(best_text)
                        print(f"[DEBUG] Added '{best_text}' to detected names")
                    else:
                        print(f"[DEBUG] Skipped '{best_text}' (empty or duplicate)")
                    # Optional: Save name box crop for debugging
                    # cv2.imwrite(f"namebox_debug_{idx}.png", denoised)
                else:
                    print(f"[DEBUG] Card {idx+1} perspective transform failed")
            
            # Create debug visualization
            debug_image = visualize_card_detections(frame, card_quads, detected_names)
            cv2.imwrite("card_detection_debug.png", debug_image)
            print(f"[DEBUG] Saved card detection visualization to 'card_detection_debug.png'")

            print(f"\n{'='*60}")
            print("🎯 FINAL RESULTS:")
            print(f"{'='*60}")
            if detected_names:
                print(f"✅ SUCCESS: Extracted card names: {', '.join([repr(n) for n in detected_names])}")
                try:
                    json_path = os.path.join(os.path.dirname(__file__), 'mtg_cards_data.json')
                    with open(json_path, 'r', encoding='utf-8') as f:
                        all_cards_data = json.load(f)
                    for i, detected_name in enumerate(detected_names):
                        print(f"\n{'='*60}")
                        print(f"CARD {i+1}/{len(detected_names)}: '{detected_name}'")
                        print(f"{'='*60}")
                        find_and_print_top_matches(detected_name, all_cards_data, top_n=8)
                except FileNotFoundError:
                    print(f"❌ Error: 'mtg_cards_data.json' not found in the script directory.")
                except json.JSONDecodeError:
                    print("❌ Error: Could not decode 'mtg_cards_data.json'. Please check if it's a valid JSON file.")
            else:
                print("❌ FAILED: Could not extract any card names")
            print(f"{'='*60}")
            print("🏁 PROCESSING COMPLETED")
            print(f"{'='*60}")
        elif mode == '2':
            cam_index = input("Enter camera index (default 1): ").strip()
            cam_index = int(cam_index) if cam_index.isdigit() else 1
            webcam_mode(cam_index)
        elif mode == '3':
            cam_index = input("Enter camera index (default 1): ").strip()
            cam_index = int(cam_index) if cam_index.isdigit() else 1
            test_card_detection_mode(cam_index)
        elif mode == '4':
            preview_all_cameras()
        elif mode == '5':
            cam_index = input("Enter camera index to test (default 1): ").strip()
            cam_index = int(cam_index) if cam_index.isdigit() else 1
            test_camera_simple(cam_index)
        elif mode == '6':
            max_index = input("Enter max camera index to scan (default 10): ").strip()
            max_index = int(max_index) if max_index.isdigit() else 10
            find_available_cameras(max_index)
        elif mode == '7':
            detect_obs_virtual_camera()
        elif mode == '8':
            show_obs_setup_instructions()
        else:
            print("❌ Invalid mode. Please enter '1', '2', '3', '4', '5', '6', '7', '8', or 'quit'.")

if __name__ == "__main__":
    main()
