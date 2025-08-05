# Magic: The Gathering Card Name Detection Tool

## Overview
`detectname.py` is an advanced computer vision and OCR (Optical Character Recognition) tool designed specifically for Magic: The Gathering card shops. It automatically detects and identifies MTG cards from images or live webcam feeds, making inventory management and card processing significantly more efficient.

## Features

### 🎯 Core Functionality
- **Multi-Mode Operation**: Image file processing, live webcam detection, and test modes
- **Advanced Card Detection**: Uses contour detection and perspective transformation to identify card boundaries
- **OCR Integration**: Leverages EasyOCR for accurate text recognition from card images
- **Smart Text Processing**: Includes common OCR error correction and fuzzy matching
- **Database Integration**: Matches detected names against MTG card database for verification

### 📷 Detection Modes

#### 1. Image File Mode
- Process individual card images or photos
- Supports multiple cards in a single image
- Automatic card boundary detection and perspective correction
- Batch processing capabilities

#### 2. Live Webcam Mode
- Real-time card detection from camera feed
- Configurable detection intervals and debouncing
- Visual feedback with detection overlays
- Audio notifications for successful detections

#### 3. Test Mode
- Debug visualization of card detection algorithms
- Performance metrics and statistics
- Camera connection testing and troubleshooting

### 🔧 Technical Features

#### Card Detection Algorithm
- **Multi-scale Processing**: Analyzes images at different scales for robust detection
- **Contour Analysis**: Uses advanced contour detection with hierarchy analysis
- **Aspect Ratio Validation**: Ensures detected regions match MTG card proportions
- **Edge Density Analysis**: Validates card-like regions based on edge characteristics
- **Color Variance Checking**: Filters out uniform regions that aren't cards

#### OCR Enhancement
- **Multiple Preprocessing Methods**: Adaptive thresholding, Otsu, and Gaussian filtering
- **Text Correction**: Fixes common OCR misreadings (e.g., "Istaid" → "Island")
- **Fuzzy Matching**: Uses sequence matching to find similar card names
- **Validation**: Ensures detected text is reasonable and card-like

#### Camera Support
- **Multi-Backend Support**: DirectShow, Media Foundation, FFMPEG, and Auto detection
- **OBS Virtual Camera Integration**: Special support for OBS Studio virtual cameras
- **Dynamic Resolution Handling**: Automatically adjusts to camera resolution changes
- **Camera Index Detection**: Scans and tests multiple camera indices

## Installation

### Prerequisites
```bash
pip install opencv-python
pip install easyocr
pip install numpy
```

### Required Files
- `mtg_cards_data.json`: MTG card database (must be in same directory)
- Camera hardware (for webcam modes)

## Usage

### Basic Usage
```bash
python detectname.py
```

### Mode Selection
The script provides an interactive menu with the following options:

1. **Image File Mode**: Process card images from files
2. **Webcam Live Mode**: Real-time detection from camera
3. **Test Card Detection Mode**: Debug and visualization mode
4. **Preview All Camera Indexes**: Test camera connections
5. **Test Camera Connection**: Diagnose camera issues
6. **Scan for Available Cameras**: Find working cameras
7. **Detect OBS Virtual Camera**: Special OBS integration
8. **Show OBS Setup Instructions**: OBS configuration help

### Image File Mode
```
Enter image path: C:/path/to/card_image.jpg
```
- Supports JPG, PNG, and other OpenCV-compatible formats
- Can process multiple cards in a single image
- Provides detailed detection results and database matches

### Webcam Mode
```
Enter camera index (default 1): 1
```
- Real-time card detection with visual feedback
- Configurable detection intervals
- Automatic card name extraction and database matching

## Configuration

### Detection Parameters
The script includes several configurable parameters for fine-tuning:

```python
# Card detection thresholds
area_lower = 0.15      # Minimum card area as fraction of image
area_upper = 0.35      # Maximum card area as fraction of image
aspect_low = 0.65      # Minimum aspect ratio (width/height)
aspect_high = 0.78     # Maximum aspect ratio

# Detection intervals
detection_interval = 0.5  # Seconds between detections
debounce_seconds = 2.0    # Minimum time between same card detections
```

### OCR Settings
```python
# Text processing thresholds
similarity_threshold = 0.6  # Minimum similarity for fuzzy matching
min_text_length = 4        # Minimum detected text length
```

## Output

### Detection Results
- **Card Names**: Extracted and corrected card names
- **Database Matches**: Top matches from MTG card database
- **Confidence Scores**: Similarity percentages for matches
- **Visual Feedback**: Detection overlays and preview images

### File Outputs
- `card_detection_debug.png`: Debug visualization of detected cards
- `products.json`: Processed card data for inventory management

## Advanced Features

### OBS Virtual Camera Support
The script includes special support for OBS Studio virtual cameras:
- Automatic detection of OBS Virtual Camera
- Optimized settings for virtual camera feeds
- Detailed setup instructions and troubleshooting

### Multi-Card Detection
- Detects multiple cards in a single image
- Handles overlapping and partially visible cards
- Provides individual processing for each detected card

### Error Handling
- Robust error handling for camera failures
- Graceful degradation when OCR fails
- Detailed error messages and troubleshooting suggestions

## Troubleshooting

### Common Issues

#### Camera Not Detected
1. Run "Test Camera Connection" mode
2. Check camera permissions in Windows
3. Try different camera indices (0, 1, 2, etc.)
4. Test with Windows Camera app first

#### Poor Detection Accuracy
1. Ensure good lighting conditions
2. Position cards clearly within the detection border
3. Avoid glare and shadows on card surfaces
4. Use higher resolution camera settings

#### OCR Errors
1. Check that cards are clearly visible
2. Ensure card names are not obscured
3. Try different card angles and positions
4. Verify `mtg_cards_data.json` is present and valid

### Performance Optimization
- Use 1280x720 resolution for best performance
- Close other camera applications
- Ensure adequate lighting
- Position cards within the detection border

## Integration

### With Other Tools
- **eBay Lister**: Outputs to `products.json` for eBay listing
- **Inventory Management**: Integrates with card shop inventory systems
- **Database Systems**: Compatible with MTG card databases

### API Integration
The script can be extended to integrate with:
- MTG card price APIs
- Inventory management systems
- E-commerce platforms
- Card grading services

## Future Development

### Potential Enhancements
1. **Machine Learning**: Implement ML-based card recognition
2. **Batch Processing**: Support for processing multiple images
3. **Cloud Integration**: Upload to cloud storage and processing
4. **Mobile Support**: Android/iOS app versions
5. **Real-time Pricing**: Integration with price APIs during detection
6. **Condition Assessment**: Automatic card condition evaluation
7. **Set Identification**: Automatic set detection from card images
8. **Foil Detection**: Identify foil vs. non-foil cards

### Performance Improvements
1. **GPU Acceleration**: CUDA/OpenCL support for faster processing
2. **Multi-threading**: Parallel processing for multiple cards
3. **Caching**: Cache frequently detected cards
4. **Optimization**: Further algorithm optimization

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review error messages for specific guidance
3. Test with different camera settings and lighting
4. Verify all dependencies are properly installed

## License

This tool is designed for Magic: The Gathering card shop automation and inventory management. 