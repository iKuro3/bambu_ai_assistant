import cv2
import numpy as np
import json
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedBambuVision:
    def __init__(self):
        self.model_cache = {}
        self.ocr_available = self._check_ocr_availability()
        
    def _check_ocr_availability(self):
        """Check if OCR is available"""
        try:
            import pytesseract
            # Test OCR with a small dummy image
            test_img = np.ones((50, 100), dtype=np.uint8) * 255
            pytesseract.image_to_string(test_img)
            return True
        except ImportError:
            logger.warning("pytesseract not installed. OCR features disabled.")
            return False
        except Exception as e:
            logger.warning(f"OCR not available: {e}")
            return False
        
    def detect_3d_model_preview(self, image):
        """Detect 3D model in the preview window using advanced CV"""
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            # Use Canny edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Find contours that might represent 3D model edges
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            model_features = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:  # Filter small noise
                    # Get bounding rectangle
                    rect = cv2.boundingRect(contour)
                    
                    # Calculate some features
                    perimeter = cv2.arcLength(contour, True)
                    circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
                    
                    model_features.append({
                        'area': area,
                        'rect': rect,
                        'circularity': circularity,
                        'complexity': len(contour)
                    })
            
            return model_features
            
        except Exception as e:
            logger.error(f"Error in 3D model detection: {e}")
            return []
    
    def analyze_print_bed(self, image):
        """Analyze the print bed area for objects and positioning"""
        try:
            if len(image.shape) != 3:
                return {'bed_detected': False, 'error': 'Invalid image format'}
                
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            
            # Define range for print bed (usually black or gray)
            bed_lower = np.array([0, 0, 0])
            bed_upper = np.array([180, 255, 100])
            bed_mask = cv2.inRange(hsv, bed_lower, bed_upper)
            
            # Find the largest rectangular area (likely the bed)
            contours, _ = cv2.findContours(bed_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                bed_contour = max(contours, key=cv2.contourArea)
                bed_rect = cv2.boundingRect(bed_contour)
                
                return {
                    'bed_detected': True,
                    'bed_area': bed_rect,
                    'bed_center': (bed_rect[0] + bed_rect[2]//2, bed_rect[1] + bed_rect[3]//2)
                }
            
            return {'bed_detected': False}
            
        except Exception as e:
            logger.error(f"Error in print bed analysis: {e}")
            return {'bed_detected': False, 'error': str(e)}
    
    def detect_ui_elements(self, image):
        """Detect specific Bambu Studio UI elements"""
        try:
            ui_elements = {}
            
            # Detect buttons (usually rounded rectangles with specific colors)
            ui_elements['buttons'] = self.find_buttons(image)
            
            # Detect progress bars
            ui_elements['progress_bars'] = self.find_progress_indicators(image)
            
            # Detect temperature displays (only if OCR is available)
            if self.ocr_available:
                ui_elements['temperature_displays'] = self.find_temperature_areas(image)
            else:
                ui_elements['temperature_displays'] = []
            
            return ui_elements
            
        except Exception as e:
            logger.error(f"Error in UI element detection: {e}")
            return {'buttons': [], 'progress_bars': [], 'temperature_displays': []}
    
    def find_buttons(self, image):
        """Find button-like UI elements"""
        try:
            buttons = []
            
            if len(image.shape) != 3:
                return buttons
                
            # Convert to different color spaces for better detection
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            
            # Common button colors in Bambu Studio
            button_colors = {
                'orange': [(10, 100, 100), (25, 255, 255)],  # Slice button
                'blue': [(100, 100, 100), (130, 255, 255)],   # Print button  
                'green': [(40, 100, 100), (80, 255, 255)],    # Ready status
                'red': [(0, 100, 100), (10, 255, 255)]        # Stop/Error
            }
            
            for color_name, (lower, upper) in button_colors.items():
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if 500 < area < 5000:  # Reasonable button size
                        rect = cv2.boundingRect(contour)
                        w, h = rect[2], rect[3]
                        
                        if h > 0:  # Prevent division by zero
                            aspect_ratio = w / h
                            
                            # Buttons usually have certain aspect ratios
                            if 1.5 < aspect_ratio < 4:
                                buttons.append({
                                    'color': color_name,
                                    'position': rect,
                                    'center': (rect[0] + rect[2]//2, rect[1] + rect[3]//2),
                                    'confidence': min(1.0, area / 2000)
                                })
            
            return buttons
            
        except Exception as e:
            logger.error(f"Error in button detection: {e}")
            return []
    
    def find_progress_indicators(self, image):
        """Find progress bars and percentage indicators"""
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            # Look for rectangular shapes that could be progress bars
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            progress_indicators = []
            
            for contour in contours:
                rect = cv2.boundingRect(contour)
                w, h = rect[2], rect[3]
                
                # Progress bars are typically wide and short
                if w > 100 and h > 10 and w > h * 3:
                    # Analyze the fill pattern
                    y1, y2 = rect[1], rect[1] + h
                    x1, x2 = rect[0], rect[0] + w
                    
                    # Check bounds
                    if y2 <= gray.shape[0] and x2 <= gray.shape[1]:
                        roi = gray[y1:y2, x1:x2]
                        
                        if roi.size > 0:
                            # Simple progress estimation
                            estimated_progress = self.estimate_progress_fill(roi)
                            progress_indicators.append({
                                'position': rect,
                                'estimated_progress': estimated_progress,
                                'type': 'horizontal_bar'
                            })
            
            return progress_indicators
            
        except Exception as e:
            logger.error(f"Error in progress indicator detection: {e}")
            return []
    
    def estimate_progress_fill(self, roi):
        """Estimate how much of a progress bar is filled"""
        try:
            if roi.size == 0:
                return 0
                
            height, width = roi.shape
            
            if width == 0:
                return 0
            
            # Scan from left to right looking for the transition point
            row_means = np.mean(roi, axis=0)
            
            if len(row_means) == 0:
                return 0
            
            # Find the point where brightness changes significantly
            diff = np.diff(row_means)
            if len(diff) == 0:
                return 0
                
            std_diff = np.std(diff)
            if std_diff == 0:
                return 0
                
            transition_points = np.where(np.abs(diff) > std_diff * 2)[0]
            
            if len(transition_points) > 0:
                # Use the first major transition as progress indicator
                progress_pixel = transition_points[0]
                return min(100, max(0, int((progress_pixel / width) * 100)))
            
            return 0
            
        except Exception as e:
            logger.error(f"Error estimating progress: {e}")
            return 0
    
    def find_temperature_areas(self, image):
        """Find areas likely to contain temperature information"""
        if not self.ocr_available:
            logger.warning("OCR not available for temperature detection")
            return []
            
        try:
            import pytesseract
            
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            # Get detailed OCR data with bounding boxes
            data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
            
            temperature_areas = []
            
            if 'text' not in data or not data['text']:
                return temperature_areas
            
            for i, text in enumerate(data['text']):
                if not text or not text.strip():
                    continue
                    
                # Look for temperature patterns
                if '°' in text or ('C' in text and any(c.isdigit() for c in text)):
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    
                    if w > 0 and h > 0:
                        # Extract the numeric value
                        import re
                        numbers = re.findall(r'\d+', text)
                        if numbers:
                            try:
                                temp_value = int(numbers[0])
                                if 20 <= temp_value <= 300:  # Reasonable temperature range
                                    temperature_areas.append({
                                        'text': text,
                                        'value': temp_value,
                                        'position': (x, y, w, h),
                                        'center': (x + w//2, y + h//2)
                                    })
                            except ValueError:
                                continue
            
            return temperature_areas
            
        except Exception as e:
            logger.error(f"OCR error in temperature detection: {e}")
            return []
    
    def generate_detailed_report(self, image):
        """Generate a comprehensive analysis report"""
        try:
            if image is None or image.size == 0:
                return {'error': 'Invalid image provided'}
                
            report = {
                'timestamp': time.time(),
                'image_dimensions': image.shape[:2] if len(image.shape) >= 2 else (0, 0),
                'model_preview': self.detect_3d_model_preview(image),
                'print_bed': self.analyze_print_bed(image),
                'ui_elements': self.detect_ui_elements(image),
                'actionable_items': []
            }
            
            # Generate actionable recommendations
            if report['ui_elements']['buttons']:
                for button in report['ui_elements']['buttons']:
                    if button['color'] == 'orange' and button['confidence'] > 0.7:
                        report['actionable_items'].append({
                            'action': 'slice_model',
                            'description': 'Slice button detected and ready to click',
                            'position': button['center'],
                            'confidence': button['confidence']
                        })
                    elif button['color'] == 'blue' and button['confidence'] > 0.7:
                        report['actionable_items'].append({
                            'action': 'start_print',
                            'description': 'Print button detected and ready to click',
                            'position': button['center'],
                            'confidence': button['confidence']
                        })
            
            if report['ui_elements']['progress_bars']:
                for pb in report['ui_elements']['progress_bars']:
                    if pb['estimated_progress'] > 0:
                        report['actionable_items'].append({
                            'action': 'monitor_progress',
                            'description': f'Print progress: {pb["estimated_progress"]}%',
                            'progress': pb['estimated_progress']
                        })
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating detailed report: {e}")
            return {'error': str(e), 'timestamp': time.time()}

# Usage functions for integration
def get_advanced_analysis(screenshot_array):
    """Main function to get advanced vision analysis"""
    try:
        if screenshot_array is None:
            return {'error': 'No screenshot provided'}
            
        vision = AdvancedBambuVision()
        return vision.generate_detailed_report(screenshot_array)
    except Exception as e:
        logger.error(f"Error in get_advanced_analysis: {e}")
        return {'error': str(e)}


