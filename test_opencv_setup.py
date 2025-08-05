#!/usr/bin/env python3

import sys

def test_imports():
    """Test if all required packages can be imported"""
    try:
        import cv2
        print(f"✅ OpenCV version: {cv2.__version__}")
    except ImportError:
        print("❌ OpenCV not found")
        return False
    
    try:
        import numpy as np
        print(f"✅ NumPy version: {np.__version__}")
    except ImportError:
        print("❌ NumPy not found")
        return False
    
    try:
        import pytesseract
        print("✅ PyTesseract imported successfully")
        # Test if tesseract executable is available
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract version: {version}")
    except ImportError:
        print("❌ PyTesseract not found")
        return False
    except Exception as e:
        print(f"⚠️  PyTesseract imported but Tesseract executable not found: {e}")
        print("Please install Tesseract OCR:")
        print("  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        print("  macOS: brew install tesseract")
        print("  Ubuntu/Debian: sudo apt-get install tesseract-ocr")
        return False
    
    try:
        import json
        import os
        import re
        from difflib import SequenceMatcher
        print("✅ Standard library modules imported successfully")
    except ImportError as e:
        print(f"❌ Standard library import error: {e}")
        return False
    
    return True

def test_opencv_functionality():
    """Test basic OpenCV functionality"""
    try:
        import cv2
        import numpy as np
        
        # Create a test image
        test_img = np.zeros((100, 100, 3), dtype=np.uint8)
        test_img.fill(255)  # White image
        
        # Test basic operations
        gray = cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        
        print("✅ OpenCV basic functionality test passed")
        return True
    except Exception as e:
        print(f"❌ OpenCV functionality test failed: {e}")
        return False

def main():
    print("🔍 Testing OpenCV Card Identifier Setup")
    print("=" * 50)
    
    if not test_imports():
        print("\n❌ Import tests failed. Please install missing packages.")
        sys.exit(1)
    
    if not test_opencv_functionality():
        print("\n❌ OpenCV functionality test failed.")
        sys.exit(1)
    
    print("\n✅ All tests passed! The OpenCV card identifier should work.")
    print("\nNext steps:")
    print("1. Make sure you have a Magic card image ready")
    print("2. Run: python gemmacardidentifier_opencv.py")
    print("3. If you have mtg_cards_data.json, it will search for matches")

if __name__ == "__main__":
    main()