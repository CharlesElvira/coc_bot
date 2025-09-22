import json
import os
import cv2
import pytesseract
import re
import time
import numpy
from adb_utils import capture_screen

def find_trophy_coordinates(screen_image_path="trophy_screen.png", template_path=None, threshold=0.6):
    """
    Find trophy symbol coordinates using template matching and return rectangle coordinates
    40 pixels high and 100 pixels wide to the right of the trophy symbol.

    
    Args:
        screen_image_path (str): Path to the screen capture image
        template_path (str): Path to trophy symbol template (defaults to src/templates/trophy_symbol.png)
        threshold (float): Matching threshold (0.0 to 1.0)

    Returns:
        tuple: (x1, y1, x2, y2) coordinates of the trophy text area, or None if not found
    """
    try:
        if template_path is None:
            template_path = os.path.join(os.path.dirname(__file__), "templates", "trophy_symbol.png")

        # Load images
        screen = cv2.imread(screen_image_path)
        template = cv2.imread(template_path)

        if screen is None or template is None:
            print(f"Error: Could not load images. Screen: {screen_image_path}, Template: {template_path}")
            return None

        # Perform template matching
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            # Get template dimensions
            template_h, template_w = template.shape[:2]

            # Trophy symbol position
            trophy_x = max_loc[0]
            trophy_y = max_loc[1]

            # Calculate rectangle to the right of trophy symbol
            # 40 pixels high, 100 pixels wide, positioned to the right
            x1 = trophy_x + template_w + 35  # 5 pixel gap from trophy
            y1 = trophy_y + (template_h - 40) // 2  # Center vertically
            x2 = x1 + 90  # 100 pixels wide
            y2 = y1 + 40   # 40 pixels high

            print(f"Trophy symbol found at ({trophy_x}, {trophy_y}) with confidence {max_val:.3f}")
            print(f"Trophy text area coordinates: ({x1}, {y1}) to ({x2}, {y2})")

            return (x1, y1, x2, y2)
        else:
            print(f"Trophy symbol not found. Best match confidence: {max_val:.3f} (threshold: {threshold})")
            return None

    except Exception as e:
        print(f"Error finding trophy coordinates: {e}")
        return None

def test_trophy_detection(screen_image_path="trophy_screen.png", output_path="trophy_debug.png", template_path=None, threshold=0.6):
    """
    Test trophy detection and export debug image with red rectangle around detected trophy area.

    Args:
        screen_image_path (str): Path to the screen capture image
        output_path (str): Path to save the debug image
        template_path (str): Path to trophy symbol template
        threshold (float): Matching threshold (0.0 to 1.0)

    Returns:
        tuple: (x1, y1, x2, y2) coordinates if found, None otherwise
    """
    try:
        if template_path is None:
            template_path = os.path.join(os.path.dirname(__file__), "templates", "trophy_symbol.png")

        # Load images
        screen = cv2.imread(screen_image_path)
        template = cv2.imread(template_path)

        if screen is None or template is None:
            print(f"Error: Could not load images. Screen: {screen_image_path}, Template: {template_path}")
            return None

        # Create a copy for drawing
        debug_image = screen.copy()

        # Perform template matching
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            # Get template dimensions
            template_h, template_w = template.shape[:2]

            # Trophy symbol position
            trophy_x = max_loc[0]
            trophy_y = max_loc[1]

            # Draw rectangle around trophy symbol (blue)
            cv2.rectangle(debug_image, (trophy_x, trophy_y),
                         (trophy_x + template_w, trophy_y + template_h), (255, 0, 0), 2)

            # Calculate rectangle to the right of trophy symbol
            x1 = trophy_x + template_w + 35
            y1 = trophy_y + (template_h - 40) // 2
            x2 = x1 + 90
            y2 = y1 + 40

            # Draw rectangle around trophy text area (red)
            cv2.rectangle(debug_image, (x1, y1), (x2, y2), (0, 0, 255), 2)

            # Add text labels
            cv2.putText(debug_image, "Trophy Symbol", (trophy_x, trophy_y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            cv2.putText(debug_image, "Trophy Text Area", (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.putText(debug_image, f"Confidence: {max_val:.3f}", (trophy_x, trophy_y + template_h + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            # Save debug image
            cv2.imwrite(output_path, debug_image)

            print(f"Trophy symbol found at ({trophy_x}, {trophy_y}) with confidence {max_val:.3f}")
            print(f"Trophy text area coordinates: ({x1}, {y1}) to ({x2}, {y2})")
            print(f"Debug image saved to: {output_path}")

            return (x1, y1, x2, y2)
        else:
            print(f"Trophy symbol not found. Best match confidence: {max_val:.3f} (threshold: {threshold})")
            # Save debug image anyway to show where it tried to match
            cv2.putText(debug_image, f"Not Found - Best: {max_val:.3f}", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imwrite(output_path, debug_image)
            print(f"Debug image saved to: {output_path}")
            return None

    except Exception as e:
        print(f"Error testing trophy detection: {e}")
        return None

def calibrate_trophy_position(x1=None, y1=None, x2=None, y2=None, auto_detect=True):
    """
    Calibrate trophy position coordinates and save to config.json
    Can use auto-detection via template matching or manual coordinates.

    Args:
        x1 (int, optional): Top-left x coordinate
        y1 (int, optional): Top-left y coordinate
        x2 (int, optional): Bottom-right x coordinate
        y2 (int, optional): Bottom-right y coordinate
        auto_detect (bool): If True, use template matching to find coordinates

    Returns:
        bool: True if successfully saved, False otherwise
    """
    try:
        if auto_detect:
            # Use template matching to find trophy coordinates
            coords = find_trophy_coordinates()
            if coords is None:
                print("Auto-detection failed. Please provide manual coordinates.")
                return False
            x1, y1, x2, y2 = coords
        elif any(coord is None for coord in [x1, y1, x2, y2]):
            print("Manual mode requires all coordinates (x1, y1, x2, y2)")
            return False

        CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config.json")

        # Read existing config
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)

        # Update trophy ROI coordinates
        config["trophy_roi"]["x1"] = x1
        config["trophy_roi"]["y1"] = y1
        config["trophy_roi"]["x2"] = x2
        config["trophy_roi"]["y2"] = y2

        # Save updated config
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)

        print(f"Trophy position calibrated: ({x1}, {y1}) to ({x2}, {y2})")
        return True

    except Exception as e:
        print(f"Error calibrating trophy position: {e}")
        return False

# COIN FUNCTIONS
def find_coin_coordinates(screen_image_path="trophy_screen.png", template_path=None, threshold=0.6):
    """
    Find coin symbol coordinates using template matching and return rectangle coordinates
    40 pixels high and 100 pixels wide to the left of the coin symbol (-290 pixels from center).

    Args:
        screen_image_path (str): Path to the screen capture image
        template_path (str): Path to coin symbol template (defaults to src/templates/coin_symbol.png)
        threshold (float): Matching threshold (0.0 to 1.0)

    Returns:
        tuple: (x1, y1, x2, y2) coordinates of the coin text area, or None if not found
    """
    try:
        if template_path is None:
            template_path = os.path.join(os.path.dirname(__file__), "templates", "coin_symbol.png")

        # Load images
        screen = cv2.imread(screen_image_path)
        template = cv2.imread(template_path)

        if screen is None or template is None:
            print(f"Error: Could not load images. Screen: {screen_image_path}, Template: {template_path}")
            return None

        # Perform template matching
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            # Get template dimensions
            template_h, template_w = template.shape[:2]

            # Coin symbol position
            coin_x = max_loc[0]
            coin_y = max_loc[1]

            # Calculate center of coin symbol
            coin_center_x = coin_x + template_w // 2
            coin_center_y = coin_y + template_h // 2

            # Calculate rectangle to the left of coin symbol (-290 pixels from center)
            x1 = coin_center_x - 310  # 50 pixels wide to the left
            y1 = coin_center_y - 20  # Center vertically (40 pixels high)
            x2 = coin_center_x - 290 + 250  # 100 pixels wide total
            y2 = coin_center_y + 20   # 40 pixels high total

            print(f"Coin symbol found at ({coin_x}, {coin_y}) with confidence {max_val:.3f}")
            print(f"Coin text area coordinates: ({x1}, {y1}) to ({x2}, {y2})")

            return (x1, y1, x2, y2)
        else:
            print(f"Coin symbol not found. Best match confidence: {max_val:.3f} (threshold: {threshold})")
            return None

    except Exception as e:
        print(f"Error finding coin coordinates: {e}")
        return None

def calibrate_coin_position(x1=None, y1=None, x2=None, y2=None, auto_detect=True):
    """
    Calibrate coin position coordinates and save to config.json
    Can use auto-detection via template matching or manual coordinates.

    Args:
        x1 (int, optional): Top-left x coordinate
        y1 (int, optional): Top-left y coordinate
        x2 (int, optional): Bottom-right x coordinate
        y2 (int, optional): Bottom-right y coordinate
        auto_detect (bool): If True, use template matching to find coordinates

    Returns:
        bool: True if successfully saved, False otherwise
    """
    try:
        if auto_detect:
            # Use template matching to find coin coordinates
            coords = find_coin_coordinates()
            if coords is None:
                print("Auto-detection failed. Please provide manual coordinates.")
                return False
            x1, y1, x2, y2 = coords
        elif any(coord is None for coord in [x1, y1, x2, y2]):
            print("Manual mode requires all coordinates (x1, y1, x2, y2)")
            return False

        CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config.json")

        # Read existing config
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)

        # Create coin_roi if it doesn't exist
        if "coin_roi" not in config:
            config["coin_roi"] = {}

        # Update coin ROI coordinates
        config["coin_roi"]["x1"] = x1
        config["coin_roi"]["y1"] = y1
        config["coin_roi"]["x2"] = x2
        config["coin_roi"]["y2"] = y2

        # Save updated config
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)

        print(f"Coin position calibrated: ({x1}, {y1}) to ({x2}, {y2})")
        return True

    except Exception as e:
        print(f"Error calibrating coin position: {e}")
        return False

def test_coin_detection(screen_image_path="trophy_screen.png", output_path="coin_debug.png", template_path=None, threshold=0.6):
    """
    Test coin detection and export debug image with rectangles around detected coin area.

    Args:
        screen_image_path (str): Path to the screen capture image
        output_path (str): Path to save the debug image
        template_path (str): Path to coin symbol template
        threshold (float): Matching threshold (0.0 to 1.0)

    Returns:
        tuple: (x1, y1, x2, y2) coordinates if found, None otherwise
    """
    try:
        if template_path is None:
            template_path = os.path.join(os.path.dirname(__file__), "templates", "coin_symbol.png")

        # Load images
        screen = cv2.imread(screen_image_path)
        template = cv2.imread(template_path)

        if screen is None or template is None:
            print(f"Error: Could not load images. Screen: {screen_image_path}, Template: {template_path}")
            return None

        # Create a copy for drawing
        debug_image = screen.copy()

        # Perform template matching
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            # Get template dimensions
            template_h, template_w = template.shape[:2]

            # Coin symbol position
            coin_x = max_loc[0]
            coin_y = max_loc[1]

            # Draw rectangle around coin symbol (blue)
            cv2.rectangle(debug_image, (coin_x, coin_y),
                         (coin_x + template_w, coin_y + template_h), (255, 0, 0), 2)

            # Calculate coin center and text area
            coin_center_x = coin_x + template_w // 2
            coin_center_y = coin_y + template_h // 2

            x1 = coin_center_x - 310
            y1 = coin_center_y - 20
            x2 = coin_center_x - 290 + 250
            y2 = coin_center_y + 20

            # Draw rectangle around coin text area (yellow)
            cv2.rectangle(debug_image, (x1, y1), (x2, y2), (0, 255, 255), 2)

            # Add text labels
            cv2.putText(debug_image, "Coin Symbol", (coin_x, coin_y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            cv2.putText(debug_image, "Coin Text Area", (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.putText(debug_image, f"Confidence: {max_val:.3f}", (coin_x, coin_y + template_h + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            # Save debug image
            cv2.imwrite(output_path, debug_image)

            print(f"Coin symbol found at ({coin_x}, {coin_y}) with confidence {max_val:.3f}")
            print(f"Coin text area coordinates: ({x1}, {y1}) to ({x2}, {y2})")
            print(f"Debug image saved to: {output_path}")

            return (x1, y1, x2, y2)
        else:
            print(f"Coin symbol not found. Best match confidence: {max_val:.3f} (threshold: {threshold})")
            cv2.putText(debug_image, f"Not Found - Best: {max_val:.3f}", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imwrite(output_path, debug_image)
            print(f"Debug image saved to: {output_path}")
            return None

    except Exception as e:
        print(f"Error testing coin detection: {e}")
        return None

def read_coins():
    """
    Read coin count from the screen using OCR on the configured coin ROI.

    Returns:
        int: Number of coins, or None if reading failed
    """
    capture_screen("trophy_screen.png")
    img = cv2.imread("trophy_screen.png")
    if img is None:
        print("Error reading captured screen!")
        return None

    CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config.json")

    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    if "coin_roi" not in config:
        print("Coin ROI not configured. Run calibrate_coin_position() first.")
        return None

    roi = config["coin_roi"]
    x1, y1, x2, y2 = roi["x1"], roi["y1"], roi["x2"], roi["y2"]

    # Crop the region of interest (ROI)
    roi = img[y1:y2, x1:x2]

    # Convert to grayscale
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # Apply threshold
    _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)

    # Use Tesseract to read the text
    config_ocr = "--psm 7 -c tessedit_char_whitelist=0123456789"
    text = pytesseract.image_to_string(thresh, config=config_ocr)

    # Extract digits from the recognized text
    match = re.findall(r"\d+", text)
    if match:
        coins_str = match[0]
        coins = int(coins_str)
        return coins
    else:
        return None

# ELIXIR FUNCTIONS
def find_elixir_coordinates(screen_image_path="trophy_screen.png", template_path=None, threshold=0.6):
    """
    Find elixir symbol coordinates using template matching and return rectangle coordinates
    40 pixels high and 100 pixels wide to the left of the elixir symbol (-290 pixels from center).

    Args:
        screen_image_path (str): Path to the screen capture image
        template_path (str): Path to elixir symbol template (defaults to src/templates/elixir_symbol.png.png)
        threshold (float): Matching threshold (0.0 to 1.0)

    Returns:
        tuple: (x1, y1, x2, y2) coordinates of the elixir text area, or None if not found
    """
    try:
        if template_path is None:
            template_path = os.path.join(os.path.dirname(__file__), "templates", "elixir_symbol.png.png")

        # Load images
        screen = cv2.imread(screen_image_path)
        template = cv2.imread(template_path)

        if screen is None or template is None:
            print(f"Error: Could not load images. Screen: {screen_image_path}, Template: {template_path}")
            return None

        # Perform template matching
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            # Get template dimensions
            template_h, template_w = template.shape[:2]

            # Elixir symbol position
            elixir_x = max_loc[0]
            elixir_y = max_loc[1]

            # Calculate center of elixir symbol
            elixir_center_x = elixir_x + template_w // 2
            elixir_center_y = elixir_y + template_h // 2

            # Calculate rectangle to the left of elixir symbol (-290 pixels from center)
            x1 = elixir_center_x - 310  # 50 pixels wide to the left
            y1 = elixir_center_y - 20  # Center vertically (40 pixels high)
            x2 = elixir_center_x - 290 + 260  # 100 pixels wide total
            y2 = elixir_center_y + 20   # 40 pixels high total

            print(f"Elixir symbol found at ({elixir_x}, {elixir_y}) with confidence {max_val:.3f}")
            print(f"Elixir text area coordinates: ({x1}, {y1}) to ({x2}, {y2})")

            return (x1, y1, x2, y2)
        else:
            print(f"Elixir symbol not found. Best match confidence: {max_val:.3f} (threshold: {threshold})")
            return None

    except Exception as e:
        print(f"Error finding elixir coordinates: {e}")
        return None

def calibrate_elixir_position(x1=None, y1=None, x2=None, y2=None, auto_detect=True):
    """
    Calibrate elixir position coordinates and save to config.json
    Can use auto-detection via template matching or manual coordinates.

    Args:
        x1 (int, optional): Top-left x coordinate
        y1 (int, optional): Top-left y coordinate
        x2 (int, optional): Bottom-right x coordinate
        y2 (int, optional): Bottom-right y coordinate
        auto_detect (bool): If True, use template matching to find coordinates

    Returns:
        bool: True if successfully saved, False otherwise
    """
    try:
        if auto_detect:
            # Use template matching to find elixir coordinates
            coords = find_elixir_coordinates()
            if coords is None:
                print("Auto-detection failed. Please provide manual coordinates.")
                return False
            x1, y1, x2, y2 = coords
        elif any(coord is None for coord in [x1, y1, x2, y2]):
            print("Manual mode requires all coordinates (x1, y1, x2, y2)")
            return False

        CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config.json")

        # Read existing config
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)

        # Create elixir_roi if it doesn't exist
        if "elixir_roi" not in config:
            config["elixir_roi"] = {}

        # Update elixir ROI coordinates
        config["elixir_roi"]["x1"] = x1
        config["elixir_roi"]["y1"] = y1
        config["elixir_roi"]["x2"] = x2
        config["elixir_roi"]["y2"] = y2

        # Save updated config
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)

        print(f"Elixir position calibrated: ({x1}, {y1}) to ({x2}, {y2})")
        return True

    except Exception as e:
        print(f"Error calibrating elixir position: {e}")
        return False

def test_elixir_detection(screen_image_path="trophy_screen.png", output_path="elixir_debug.png", template_path=None, threshold=0.6):
    """
    Test elixir detection and export debug image with rectangles around detected elixir area.

    Args:
        screen_image_path (str): Path to the screen capture image
        output_path (str): Path to save the debug image
        template_path (str): Path to elixir symbol template
        threshold (float): Matching threshold (0.0 to 1.0)

    Returns:
        tuple: (x1, y1, x2, y2) coordinates if found, None otherwise
    """
    try:
        if template_path is None:
            template_path = os.path.join(os.path.dirname(__file__), "templates", "elixir_symbol.png.png")

        # Load images
        screen = cv2.imread(screen_image_path)
        template = cv2.imread(template_path)

        if screen is None or template is None:
            print(f"Error: Could not load images. Screen: {screen_image_path}, Template: {template_path}")
            return None

        # Create a copy for drawing
        debug_image = screen.copy()

        # Perform template matching
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            # Get template dimensions
            template_h, template_w = template.shape[:2]

            # Elixir symbol position
            elixir_x = max_loc[0]
            elixir_y = max_loc[1]

            # Draw rectangle around elixir symbol (blue)
            cv2.rectangle(debug_image, (elixir_x, elixir_y),
                         (elixir_x + template_w, elixir_y + template_h), (255, 0, 0), 2)

            # Calculate elixir center and text area
            elixir_center_x = elixir_x + template_w // 2
            elixir_center_y = elixir_y + template_h // 2

            x1 = elixir_center_x - 310
            y1 = elixir_center_y - 20
            x2 = elixir_center_x - 290 + 260
            y2 = elixir_center_y + 20

            # Draw rectangle around elixir text area (magenta)
            cv2.rectangle(debug_image, (x1, y1), (x2, y2), (255, 0, 255), 2)

            # Add text labels
            cv2.putText(debug_image, "Elixir Symbol", (elixir_x, elixir_y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            cv2.putText(debug_image, "Elixir Text Area", (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
            cv2.putText(debug_image, f"Confidence: {max_val:.3f}", (elixir_x, elixir_y + template_h + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            # Save debug image
            cv2.imwrite(output_path, debug_image)

            print(f"Elixir symbol found at ({elixir_x}, {elixir_y}) with confidence {max_val:.3f}")
            print(f"Elixir text area coordinates: ({x1}, {y1}) to ({x2}, {y2})")
            print(f"Debug image saved to: {output_path}")

            return (x1, y1, x2, y2)
        else:
            print(f"Elixir symbol not found. Best match confidence: {max_val:.3f} (threshold: {threshold})")
            cv2.putText(debug_image, f"Not Found - Best: {max_val:.3f}", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imwrite(output_path, debug_image)
            print(f"Debug image saved to: {output_path}")
            return None

    except Exception as e:
        print(f"Error testing elixir detection: {e}")
        return None

def read_elixir():
    """
    Read elixir count from the screen using OCR on the configured elixir ROI.

    Returns:
        int: Number of elixir, or None if reading failed
    """
    capture_screen("trophy_screen.png")
    img = cv2.imread("trophy_screen.png")
    if img is None:
        print("Error reading captured screen!")
        return None

    CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config.json")

    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    if "elixir_roi" not in config:
        print("Elixir ROI not configured. Run calibrate_elixir_position() first.")
        return None

    roi = config["elixir_roi"]
    x1, y1, x2, y2 = roi["x1"], roi["y1"], roi["x2"], roi["y2"]

    # Crop the region of interest (ROI)
    roi = img[y1:y2, x1:x2]

    # Convert to grayscale
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # Apply threshold
    _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)

    # Use Tesseract to read the text
    config_ocr = "--psm 7 -c tessedit_char_whitelist=0123456789"
    text = pytesseract.image_to_string(thresh, config=config_ocr)

    # Extract digits from the recognized text
    match = re.findall(r"\d+", text)
    if match:
        elixir_str = match[0]
        elixir = int(elixir_str)
        return elixir
    else:
        return None

def read_trophies():
    capture_screen("trophy_screen.png")
    img = cv2.imread("trophy_screen.png")
    if img is None:
        print("Error reading captured screen!")
        return None
    
    CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config.json")

    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    roi = config["trophy_roi"]
    x1, y1, x2, y2 = roi["x1"], roi["y1"], roi["x2"], roi["y2"]

    # Crop the region of interest (ROI)
    roi = img[y1:y2, x1:x2]

    # Convert to grayscale
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # Optionally apply a threshold to darken text
    # You may need to experiment with thresholds or other preprocessing
    _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)

    # Use Tesseract to read the text
    # --psm 7 helps Tesseract focus on a single line/number
    config = "--psm 7 -c tessedit_char_whitelist=0123456789"
    text = pytesseract.image_to_string(thresh, config=config)

    # Extract digits from the recognized text
    match = re.findall(r"\d+", text)
    if match:
        trophies_str = match[0]  # e.g. "2922"
        trophies = int(trophies_str)
        return trophies
    else:
        return None
    
def find_template(template_path, threshold=0.60):
    """
    Capture the screen and search for the template image.
    Returns the center coordinates of the match if confidence ≥ threshold; otherwise None.
    """
    capture_screen()
    screen = cv2.imread("screen.png")
    template = cv2.imread(template_path)
    if screen is None or template is None:
        print(f"Error: Could not load images for {template_path}.")
        return None
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val >= threshold:
        t_h, t_w = template.shape[:2]
        return (max_loc[0] + t_w // 2, max_loc[1] + t_h // 2)
    return None

def wait_for_template(template_path, timeout=3, threshold=0.6):
    """
    Searches for a template image on screen for up to `timeout` seconds.
    If found, returns the coordinates (with random jitter ±10 pixels); otherwise, returns None.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        coords = find_template(template_path, threshold)
        if coords:
            return (coords[0], coords[1])
    return None

# def read_resources():
#     capture_screen("resources_screen.png")
#     img = cv2.imread("resources_screen.png")
#     if img is None:
#         print("Error reading captured screen!")
#         return None
#     x1G, y1G = 170, 150   # top-left corner of ROI FOR GOLD    
#     x2G, y2G = 345, 185  # bottom-right corner of ROI FOR GOLD
#     x1E, y1E = 170, 205   # top-left corner of ROI FOR ELIXIR
#     x2E, y2E = 345, 240  # bottom-right corner of ROI FOR EL
#     roi_gold = img[y1G:y2G, x1G:x2G]
#     roi_elixir = img[y1E:y2E, x1E:x2E]

#     # convert the ROI to HSV color space
#     roi_gold_hsv = cv2.cvtColor(roi_gold, cv2.COLOR_BGR2HSV)
#     roi_elixir_hsv = cv2.cvtColor(roi_elixir, cv2.COLOR_BGR2HSV)
#     # define the lower and upper bounds for the color in bgr
#     lower_bound_gold = np.array([10, 40, 201])  # BGR for gold color
#     upper_bound_gold = np.array([40, 75, 255])  # BGR for gold color
#     lower_bound_elixir = np.array([150, 0, 170])  # BGR for elixir color  
#     upper_bound_elixir = np.array([179, 40, 255])  # BGR for elixir color
    
#     # create a mask for the gold color
#     mask_gold = cv2.inRange(roi_gold_hsv, lower_bound_gold, upper_bound_gold)
#     # create a mask for the elixir color
#     mask_elixir = cv2.inRange(roi_elixir_hsv, lower_bound_elixir, upper_bound_elixir)

#     config = "--psm 7 -c tessedit_char_whitelist=0123456789"
#     text_gold = pytesseract.image_to_string(mask_gold, config=config)
#     text_elixir = pytesseract.image_to_string(mask_elixir, config=config)
#     match_gold = re.findall(r"\d+", text_gold)
#     match_elixir = re.findall(r"\d+", text_elixir)
#     gold = 0
#     elixir = 0
#     if match_gold:
#         gold_str = match_gold[0]
#         gold = int(gold_str)
#     if match_elixir:
#         elixir_str = match_elixir[0]
#         elixir = int(elixir_str)
#     print(f"Gold: {gold}, Elixir: {elixir}")    
#     ressources = gold + elixir
#     return ressources

# def read_percentage():
#     # Capture the screen and read the percentage from the current attack 
#     # mainly to stop the attack before 100% to stay as much as possible in fake legends
#     capture_screen("percentage_screen.png")
#     img = cv2.imread("percentage_screen.png")
#     if img is None:
#         print("Error reading captured screen!")
#         return None
#     # unique. just check on your device if you want to change it
#     x1, y1 = 2140, 828  # top-left corner of ROI
#     x2, y2 = 2240, 872  # bottom-right corner of ROI
#     roi = img[y1:y2, x1:x2]
#     gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
#     _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_OTSU)
#     kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
#     eroded_image = cv2.erode(thresh, kernel, iterations=1)
#     config = "--psm 7 -c tessedit_char_whitelist=0123456789%"
#     text = pytesseract.image_to_string(eroded_image, config=config)
#     match = re.findall(r"\d+", text)
#     if match:
#         percentage_str = match[0]
#         percentage = int(percentage_str)
#         return percentage
#     else:
#         return None