# REPLACE FILE: realtime_helper.py
# This replaces your existing empty realtime_helper.py with AI vision capabilities

import cv2
import numpy as np
import pytesseract
import pyautogui
import time
import json
from datetime import datetime

class BambuVisionHelper:
    def __init__(self):
        self.templates = {}
        self.load_ui_templates()
        
    def load_ui_templates(self):
        """Load UI element templates for template matching"""
        # You would save screenshots of UI elements and load them here
        # For now, we'll use color-based detection
        pass
    
    def detect_print_status(self, image):
        """Detect current print status from screen"""
        status_indicators = {
            "printing": self.detect_color_indicator(image, "green"),
            "heating": self.detect_color_indicator(image, "red"),
            "paused": self.detect_color_indicator(image, "yellow"),
            "completed": self.detect_text_pattern(image, ["complete", "finished"]),
            "error": self.detect_text_pattern(image, ["error", "failed"])
        }
        
        return {k: v for k, v in status_indicators.items() if v}
    
    def detect_color_indicator(self, image, color_name):
        """Detect colored status indicators"""
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        
        color_ranges = {
            "green": [(40, 50, 50), (80, 255, 255)],
            "red": [(0, 50, 50), (10, 255, 255)],
            "yellow": [(20, 50, 50), (30, 255, 255)],
            "blue": [(100, 50, 50), (130, 255, 255)]
        }
        
        if color_name not in color_ranges:
            return False
            
        lower, upper = color_ranges[color_name]
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
        
        # Find contours and check if any are significant
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 100:  # Minimum area for status indicator
                return True
        
        return False
    
    def detect_text_pattern(self, image, patterns):
        """Detect text patterns in image"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            text = pytesseract.image_to_string(gray).lower()
            
            return any(pattern in text for pattern in patterns)
        except:
            return False
    
    def extract_temperature_info(self, image):
        """Extract temperature information from display"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            text = pytesseract.image_to_string(gray)
            
            # Look for temperature patterns like "200°C" or "200C"
            import re
            temp_pattern = r'(\d{1,3})[°]?[CF]'
            temperatures = re.findall(temp_pattern, text)
            
            return [int(temp) for temp in temperatures if int(temp) > 20]
        except:
            return []
    
    def detect_progress_bar(self, image):
        """Detect print progress from progress bars"""
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Look for horizontal progress bars (rectangular shapes with specific aspect ratio)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        progress_bars = []
        for contour in contours:
            rect = cv2.boundingRect(contour)
            w, h = rect[2], rect[3]
            
            # Progress bars are typically wide and short
            if w > h * 3 and w > 100 and h > 10:
                # Analyze the fill level
                roi = gray[rect[1]:rect[1]+h, rect[0]:rect[0]+w]
                fill_percentage = self.analyze_fill_level(roi)
                progress_bars.append({
                    'position': rect,
                    'progress': fill_percentage
                })
        
        return progress_bars
    
    def analyze_fill_level(self, roi):
        """Analyze how much of a progress bar is filled"""
        # Simple method: compare left and right halves
        mid = roi.shape[1] // 2
        left_mean = np.mean(roi[:, :mid])
        right_mean = np.mean(roi[:, mid:])
        
        # If left is significantly darker/lighter than right, estimate fill
        if abs(left_mean - right_mean) > 20:
            return min(100, max(0, int((left_mean - right_mean + 50) * 2)))
        
        return 0
    
    def get_model_info(self, image):
        """Extract 3D model information from screen"""
        info = {}
        
        try:
            # Extract text for model name, file size, etc.
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            text = pytesseract.image_to_string(gray)
            
            # Look for common 3D printing terms
            lines = text.split('\n')
            for line in lines:
                line = line.strip().lower()
                if 'layer' in line and 'mm' in line:
                    info['layer_height'] = line
                elif 'filament' in line:
                    info['filament_info'] = line
                elif '.3mf' in line or '.stl' in line:
                    info['model_file'] = line
                elif 'time' in line and ('h' in line or 'min' in line):
                    info['print_time'] = line
            
        except:
            pass
        
        return info
    
    def smart_click_suggestion(self, image, user_intent):
        """Suggest where to click based on user intent"""
        suggestions = []
        
        if "slice" in user_intent.lower():
            # Look for slice/prepare button (usually orange or green)
            slice_buttons = self.find_buttons_by_color(image, "orange") + \
                          self.find_buttons_by_color(image, "green")
            suggestions.extend([("Slice button", pos) for pos in slice_buttons])
        
        elif "print" in user_intent.lower():
            # Look for print/send button
            print_buttons = self.find_buttons_by_color(image, "blue") + \
                           self.find_buttons_by_color(image, "green")
            suggestions.extend([("Print button", pos) for pos in print_buttons])
        
        elif "settings" in user_intent.lower():
            # Look for gear icons or settings text
            settings_areas = self.find_text_areas(image, ["settings", "config"])
            suggestions.extend([("Settings area", pos) for pos in settings_areas])
        
        return suggestions
    
    def find_buttons_by_color(self, image, color_name):
        """Find button-like shapes with specific colors"""
        detected = self.detect_color_indicator(image, color_name)
        if not detected:
            return []
        
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        color_ranges = {
            "orange": [(10, 50, 50), (25, 255, 255)],
            "green": [(40, 50, 50), (80, 255, 255)],
            "blue": [(100, 50, 50), (130, 255, 255)]
        }
        
        if color_name not in color_ranges:
            return []
        
        lower, upper = color_ranges[color_name]
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        button_positions = []
        for contour in contours:
            # Check if contour is button-like (rectangular, reasonable size)
            rect = cv2.boundingRect(contour)
            w, h = rect[2], rect[3]
            
            if 50 < w < 200 and 20 < h < 60:  # Typical button dimensions
                center = (rect[0] + w//2, rect[1] + h//2)
                button_positions.append(center)
        
        return button_positions
    
    def find_text_areas(self, image, text_patterns):
        """Find areas containing specific text"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Use pytesseract to get bounding boxes of text
            data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
            
            positions = []
            for i, text in enumerate(data['text']):
                if any(pattern in text.lower() for pattern in text_patterns):
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    if w > 0 and h > 0:
                        center = (x + w//2, y + h//2)
                        positions.append(center)
            
            return positions
        except:
            return []
    
    def generate_action_report(self, image):
        """Generate a comprehensive report of what's visible and actionable"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'status': self.detect_print_status(image),
            'temperatures': self.extract_temperature_info(image),
            'progress': self.detect_progress_bar(image),
            'model_info': self.get_model_info(image),
            'suggested_actions': []
        }
        
        # Add contextual suggestions
        if report['status'].get('heating'):
            report['suggested_actions'].append("Printer is heating - wait before starting print")
        elif report['status'].get('printing'):
            report['suggested_actions'].append("Print in progress - monitor temperature and progress")
        elif not report['status']:
            report['suggested_actions'].append("Printer appears idle - ready for new print job")
        
        return report

# Usage example functions
def analyze_bambu_screen():
    """Main function to analyze current Bambu Studio screen"""
    helper = BambuVisionHelper()
    
    # Capture screen
    screenshot = pyautogui.screenshot()
    image = np.array(screenshot)
    
    # Generate comprehensive report
    report = helper.generate_action_report(image)
    
    return report

def get_smart_suggestions(user_query):
    """Get AI suggestions based on current screen and user query"""
    helper = BambuVisionHelper()
    
    screenshot = pyautogui.screenshot()
    image = np.array(screenshot)
    
    suggestions = helper.smart_click_suggestion(image, user_query)
    report = helper.generate_action_report(image)
    
    return {
        'suggestions': suggestions,
        'current_state': report,
        'recommendations': generate_recommendations(report, user_query)
    }

def generate_recommendations(report, user_query):
    """Generate smart recommendations based on current state and user intent"""
    recommendations = []
    
    query_lower = user_query.lower()
    
    if "slice" in query_lower:
        if not report['model_info']:
            recommendations.append("Load a 3D model first before slicing")
        elif report['status'].get('printing'):
            recommendations.append("Wait for current print to finish before slicing new model")
        else:
            recommendations.append("Model loaded - ready to slice")
    
    elif "print" in query_lower:
        if report['status'].get('heating'):
            recommendations.append("Printer is heating - print will start automatically when ready")
        elif report['status'].get('printing'):
            recommendations.append("Printer is already printing")
        elif not report['temperatures']:
            recommendations.append("Check printer connection and power")
        else:
            recommendations.append("Ready to start print")
    
    return recommendations