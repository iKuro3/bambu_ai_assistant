# CREATE NEW FILE: advanced_vision.py (OPTIONAL)
# This adds more advanced AI vision capabilities
# Only create this if you want extra features like object detection

import cv2
import numpy as np
from PIL import Image
import json

class AdvancedBambuVision:
    def __init__(self):
        self.model_cache = {}
        
    def detect_3d_model_preview(self, image):
        """Detect 3D model in the preview window using advanced CV"""
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
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
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                
                model_features.append({
                    'area': area,
                    'rect': rect,
                    'circularity': circularity,
                    'complexity': len(contour)
                })
        
        return model_features
    
    def analyze_print_bed(self, image):
        """Analyze the print bed area for objects and positioning"""
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
    
    def detect_ui_elements(self, image):
        """Detect specific Bambu Studio UI elements"""
        ui_elements = {}
        
        # Template matching would go here if we had UI templates
        # For now, use color and shape detection
        
        # Detect buttons (usually rounded rectangles with specific colors)
        ui_elements['buttons'] = self.find_buttons(image)
        
        # Detect progress bars
        ui_elements['progress_bars'] = self.find_progress_indicators(image)
        
        # Detect temperature displays (usually numeric text)
        ui_elements['temperature_displays'] = self.find_temperature_areas(image)
        
        return ui_elements
    
    def find_buttons(self, image):
        """Find button-like UI elements"""
        buttons = []
        
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
                    aspect_ratio = rect[2] / rect[3]
                    
                    # Buttons usually have certain aspect ratios
                    if 1.5 < aspect_ratio < 4:
                        buttons.append({
                            'color': color_name,
                            'position': rect,
                            'center': (rect[0] + rect[2]//2, rect[1] + rect[3]//2),
                            'confidence': min(1.0, area / 2000)
                        })
        
        return buttons
    
    def find_progress_indicators(self, image):
        """Find progress bars and percentage indicators"""
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
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
                roi = gray[rect[1]:rect[1]+h, rect[0]:rect[0]+w]
                
                # Simple progress estimation
                left_third = np.mean(roi[:, :w//3])
                right_third = np.mean(roi[:, 2*w//3:])
                
                # If there's a significant difference, it might be a progress bar
                if abs(left_third - right_third) > 20:
                    estimated_progress = self.estimate_progress_fill(roi)
                    progress_indicators.append({
                        'position': rect,
                        'estimated_progress': estimated_progress,
                        'type': 'horizontal_bar'
                    })
        
        return progress_indicators
    
    def estimate_progress_fill(self, roi):
        """Estimate how much of a progress bar is filled"""
        height, width = roi.shape
        
        # Scan from left to right looking for the transition point
        row_means = np.mean(roi, axis=0)
        
        # Find the point where brightness changes significantly
        diff = np.diff(row_means)
        transition_points = np.where(np.abs(diff) > np.std(diff) * 2)[0]
        
        if len(transition_points) > 0:
            # Use the first major transition as progress indicator
            progress_pixel = transition_points[0]
            return min(100, max(0, int((progress_pixel / width) * 100)))
        
        return 0
    
    def find_temperature_areas(self, image):
        """Find areas likely to contain temperature information"""
        # This would use OCR to find number patterns like "200°C"
        import pytesseract
        
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Get detailed OCR data with bounding boxes
            data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
            
            temperature_areas = []
            
            for i, text in enumerate(data['text']):
                # Look for temperature patterns
                if '°' in text or ('C' in text and any(c.isdigit() for c in text)):
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    
                    if w > 0 and h > 0:
                        # Extract the numeric value
                        import re
                        numbers = re.findall(r'\d+', text)
                        if numbers:
                            temp_value = int(numbers[0])
                            if 20 <= temp_value <= 300:  # Reasonable temperature range
                                temperature_areas.append({
                                    'text': text,
                                    'value': temp_value,
                                    'position': (x, y, w, h),
                                    'center': (x + w//2, y + h//2)
                                })
            
            return temperature_areas
            
        except Exception as e:
            print(f"OCR error in temperature detection: {e}")
            return []
    
    def generate_detailed_report(self, image):
        """Generate a comprehensive analysis report"""
        report = {
            'timestamp': json.dumps(time.time()),
            'image_dimensions': image.shape[:2],
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

# Usage functions for integration
def get_advanced_analysis(screenshot_array):
    """Main function to get advanced vision analysis"""
    vision = AdvancedBambuVision()
    return vision.generate_detailed_report(screenshot_array)

def find_clickable_elements(screenshot_array, intent=""):
    """Find elements that can be clicked based on user intent"""
    vision = AdvancedBambuVision()
    ui_elements = vision.detect_ui_elements(screenshot_array)
    
    clickable = []
    intent_lower = intent.lower()
    
    for button in ui_elements.get('buttons', []):
        if 'slice' in intent_lower and button['color'] == 'orange':
            clickable.append(('Slice Button', button['center']))
        elif 'print' in intent_lower and button['color'] == 'blue':
            clickable.append(('Print Button', button['center']))
        elif 'stop' in intent_lower and button['color'] == 'red':
            clickable.append(('Stop Button', button['center']))
    
    return clickable