# REPLACE FILE: chat_gui.py
# This replaces your existing chat_gui.py with enhanced screen vision capabilities

import customtkinter as ctk
import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
from PIL import Image, ImageTk
import threading
import time
import pytesseract
from chat_api_client import ChatAPIClient

# Configure pyautogui
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

# Configure appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class BambuAIAssistant(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Bambu AI Assistant - Live Vision")
        self.geometry("800x700")

        # Initialize variables
        self.bambu_window = None
        self.screen_capture_active = False
        self.current_screenshot = None
        self.vision_analysis = ""
        self.api_client = ChatAPIClient()
        
        self.setup_ui()
        self.find_bambu_studio()
        
    def setup_ui(self):
        # Main container
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Status bar
        self.status_frame = ctk.CTkFrame(self.main_frame)
        self.status_frame.pack(fill="x", padx=5, pady=5)
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="Status: Looking for Bambu Studio...")
        self.status_label.pack(side="left", padx=10, pady=5)
        
        self.vision_toggle = ctk.CTkSwitch(
            self.status_frame, 
            text="Live Vision", 
            command=self.toggle_vision
        )
        self.vision_toggle.pack(side="right", padx=10, pady=5)
        
        # Screen preview (small)
        self.preview_frame = ctk.CTkFrame(self.main_frame)
        self.preview_frame.pack(fill="x", padx=5, pady=5)
        
        self.preview_label = ctk.CTkLabel(self.preview_frame, text="Screen Preview")
        self.preview_label.pack(pady=5)
        
        self.screen_preview = ctk.CTkLabel(self.preview_frame, text="No preview available")
        self.screen_preview.pack(pady=5)
        
        # Vision analysis
        self.analysis_frame = ctk.CTkFrame(self.main_frame)
        self.analysis_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(self.analysis_frame, text="AI Vision Analysis:").pack(anchor="w", padx=10, pady=5)
        
        self.analysis_text = ctk.CTkTextbox(self.analysis_frame, height=100)
        self.analysis_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Chat interface
        self.chat_frame = ctk.CTkFrame(self.main_frame)
        self.chat_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(self.chat_frame, text="Chat with AI:").pack(anchor="w", padx=10, pady=5)
        
        self.chat_log = ctk.CTkTextbox(self.chat_frame, height=200)
        self.chat_log.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Input area
        self.input_frame = ctk.CTkFrame(self.main_frame)
        self.input_frame.pack(fill="x", padx=5, pady=5)
        
        self.entry = ctk.CTkEntry(self.input_frame, placeholder_text="Ask about what you see or give commands...")
        self.entry.pack(side="left", fill="x", expand=True, padx=10, pady=5)
        self.entry.bind("<Return>", self.process_input)
        
        self.send_button = ctk.CTkButton(self.input_frame, text="Send", command=self.process_input)
        self.send_button.pack(side="right", padx=10, pady=5)
        
    def find_bambu_studio(self):
        """Find Bambu Studio window"""
        try:
            windows = gw.getAllWindows()
            for window in windows:
                if "bambu" in window.title.lower() or "studio" in window.title.lower():
                    self.bambu_window = window
                    self.status_label.configure(text=f"Status: Connected to {window.title}")
                    return True
            self.status_label.configure(text="Status: Bambu Studio not found")
            return False
        except Exception as e:
            self.status_label.configure(text=f"Status: Error - {str(e)}")
            return False
    
    def toggle_vision(self):
        """Toggle live vision capture"""
        if self.vision_toggle.get():
            self.screen_capture_active = True
            self.start_vision_thread()
        else:
            self.screen_capture_active = False
    
    def start_vision_thread(self):
        """Start the vision capture thread"""
        vision_thread = threading.Thread(target=self.vision_loop, daemon=True)
        vision_thread.start()
    
    def vision_loop(self):
        """Main vision capture loop"""
        while self.screen_capture_active:
            try:
                self.capture_and_analyze()
                time.sleep(2)  # Analyze every 2 seconds
            except Exception as e:
                print(f"Vision error: {e}")
                time.sleep(1)
    
    def capture_screen(self):
        """Capture Bambu Studio window or full screen"""
        try:
            if self.bambu_window and self.bambu_window.isActive:
                # Capture specific window
                bbox = (self.bambu_window.left, self.bambu_window.top, 
                       self.bambu_window.right, self.bambu_window.bottom)
                screenshot = pyautogui.screenshot(region=bbox)
            else:
                # Capture full screen
                screenshot = pyautogui.screenshot()
            
            return np.array(screenshot)
        except Exception as e:
            print(f"Screenshot error: {e}")
            return None
    
    def analyze_screen_content(self, image):
        """Analyze screen content using computer vision"""
        analysis = []
        
        try:
            # Convert to grayscale for text detection
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Text extraction
            try:
                text = pytesseract.image_to_string(gray)
                if text.strip():
                    bambu_keywords = ['print', 'filament', 'bed', 'temperature', 'layer', 'speed']
                    found_keywords = [word for word in bambu_keywords if word in text.lower()]
                    if found_keywords:
                        analysis.append(f"Detected Bambu Studio elements: {', '.join(found_keywords)}")
            except:
                pass
            
            # Color analysis for status indicators
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            
            # Check for green (ready/good status)
            green_mask = cv2.inRange(hsv, np.array([40, 50, 50]), np.array([80, 255, 255]))
            green_pixels = cv2.countNonZero(green_mask)
            
            # Check for red (error/heating)
            red_mask1 = cv2.inRange(hsv, np.array([0, 50, 50]), np.array([10, 255, 255]))
            red_mask2 = cv2.inRange(hsv, np.array([170, 50, 50]), np.array([180, 255, 255]))
            red_pixels = cv2.countNonZero(red_mask1) + cv2.countNonZero(red_mask2)
            
            # Check for blue (cooling/info)
            blue_mask = cv2.inRange(hsv, np.array([100, 50, 50]), np.array([130, 255, 255]))
            blue_pixels = cv2.countNonZero(blue_mask)
            
            total_pixels = image.shape[0] * image.shape[1]
            
            if green_pixels > total_pixels * 0.01:
                analysis.append("🟢 Green indicators detected (possibly ready/good status)")
            if red_pixels > total_pixels * 0.01:
                analysis.append("🔴 Red indicators detected (possibly heating/error)")
            if blue_pixels > total_pixels * 0.01:
                analysis.append("🔵 Blue indicators detected (possibly cooling/info)")
            
            # Edge detection for model preview
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if len(contours) > 10:
                analysis.append(f"📐 Detected {len(contours)} shapes/objects (possibly 3D model preview)")
            
        except Exception as e:
            analysis.append(f"Analysis error: {str(e)}")
        
        return analysis if analysis else ["Screen captured, no specific patterns detected"]
    
    def capture_and_analyze(self):
        """Capture screen and perform analysis"""
        screenshot = self.capture_screen()
        if screenshot is not None:
            self.current_screenshot = screenshot
            
            # Create thumbnail for preview
            thumbnail = Image.fromarray(screenshot)
            thumbnail.thumbnail((200, 150))
            thumbnail_tk = ImageTk.PhotoImage(thumbnail)
            
            # Update preview (must be done in main thread)
            self.after(0, self.update_preview, thumbnail_tk)
            
            # Analyze content
            analysis = self.analyze_screen_content(screenshot)
            analysis_text = "\n".join(analysis)
            
            # Update analysis (must be done in main thread)
            self.after(0, self.update_analysis, analysis_text)
    
    def update_preview(self, thumbnail_tk):
        """Update screen preview in UI"""
        self.screen_preview.configure(image=thumbnail_tk, text="")
        self.screen_preview.image = thumbnail_tk  # Keep reference
    
    def update_analysis(self, analysis_text):
        """Update analysis text in UI"""
        self.analysis_text.delete(1.0, "end")
        self.analysis_text.insert(1.0, analysis_text)
    
    def control_bambu_studio(self, action):
        """Control Bambu Studio through GUI automation"""
        if not self.bambu_window:
            return "Bambu Studio window not found"
        
        try:
            # Bring Bambu Studio to front
            self.bambu_window.activate()
            time.sleep(0.5)
            
            if action == "slice":
                # Try to find and click slice button (you may need to adjust coordinates)
                pyautogui.hotkey('ctrl', 's')  # Common shortcut for slice
                return "Attempted to slice model"
            
            elif action == "print":
                pyautogui.hotkey('ctrl', 'p')  # Common shortcut for print
                return "Attempted to start print"
            
            elif action == "open":
                pyautogui.hotkey('ctrl', 'o')  # Open file
                return "Attempted to open file dialog"
            
            elif action == "center":
                # This might vary based on Bambu Studio version
                pyautogui.hotkey('ctrl', 'alt', 'c')
                return "Attempted to center model"
            
            else:
                return f"Unknown action: {action}"
                
        except Exception as e:
            return f"Control error: {str(e)}"
    
    def process_input(self, event=None):
        """Process user input and stream AI response."""
        user_input = self.entry.get().strip()
        if not user_input:
            return

        self.chat_log.insert("end", f"You: {user_input}\n")
        self.entry.delete(0, "end")

        def stream_reply():
            for chunk in self.api_client.send(user_input):
                self.chat_log.insert("end", chunk)
                self.chat_log.see("end")
                self.update()
            self.chat_log.insert("end", "\n")

        threading.Thread(target=stream_reply, daemon=True).start()

if __name__ == "__main__":
    app = BambuAIAssistant()
