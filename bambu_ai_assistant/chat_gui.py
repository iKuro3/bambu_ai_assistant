diff --git a/bambu_ai_assistant/chat_gui.py b/bambu_ai_assistant/chat_gui.py
index 7bd98b697d6b19fddd6b307de0b6b29ae64cb259..9899c2e64fe95fae773c3ddb3058c27da05efa2a 100644
--- a/bambu_ai_assistant/chat_gui.py
+++ b/bambu_ai_assistant/chat_gui.py
@@ -1,56 +1,60 @@
 import customtkinter as ctk
 import cv2
 import numpy as np
-import pyautogui
-import pygetwindow as gw
-from PIL import Image, ImageTk
-import threading
-import time
-import pytesseract
-from chat_api_client import ChatAPIClient
+import pyautogui
+import pygetwindow as gw
+from PIL import Image, ImageTk
+import mss
+import threading
+import time
+import pytesseract
+from chat_api_client import ChatAPIClient
 
 # Configure pyautogui
 pyautogui.FAILSAFE = True
 pyautogui.PAUSE = 0.1
 
 # Configure appearance
-ctk.set_appearance_mode("dark")
-ctk.set_default_color_theme("blue")
+ctk.set_appearance_mode("dark")
+ctk.set_default_color_theme("blue")
+
+CAPTURE_INTERVAL = 2.0
 
-class BambuAIAssistant(ctk.CTk):
-    def __init__(self):
-        super().__init__()
-        self.title("Bambu AI Assistant - Live Vision")
-        self.geometry("800x700")
+class BambuAIAssistant(ctk.CTk):
+    def __init__(self, capture_interval: float = CAPTURE_INTERVAL):
+        super().__init__()
+        self.title("Bambu AI Assistant - Live Vision")
+        self.geometry("800x700")
 
         # Initialize variables
         self.bambu_window = None
         self.screen_capture_active = False
-        self.current_screenshot = None
-        self.vision_analysis = ""
-        self.api_client = ChatAPIClient()
+        self.current_screenshot = None
+        self.vision_analysis = ""
+        self.capture_interval = capture_interval
+        self.api_client = ChatAPIClient()
         
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
diff --git a/bambu_ai_assistant/chat_gui.py b/bambu_ai_assistant/chat_gui.py
index 7bd98b697d6b19fddd6b307de0b6b29ae64cb259..9899c2e64fe95fae773c3ddb3058c27da05efa2a 100644
--- a/bambu_ai_assistant/chat_gui.py
+++ b/bambu_ai_assistant/chat_gui.py
@@ -101,72 +105,77 @@ class BambuAIAssistant(ctk.CTk):
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
-                self.capture_and_analyze()
-                time.sleep(2)  # Analyze every 2 seconds
+                self.capture_and_analyze()
+                time.sleep(self.capture_interval)
             except Exception as e:
                 print(f"Vision error: {e}")
                 time.sleep(1)
     
-    def capture_screen(self):
-        """Capture Bambu Studio window or full screen"""
-        try:
-            if self.bambu_window and self.bambu_window.isActive:
-                # Capture specific window
-                bbox = (self.bambu_window.left, self.bambu_window.top, 
-                       self.bambu_window.right, self.bambu_window.bottom)
-                screenshot = pyautogui.screenshot(region=bbox)
-            else:
-                # Capture full screen
-                screenshot = pyautogui.screenshot()
-            
-            return np.array(screenshot)
-        except Exception as e:
-            print(f"Screenshot error: {e}")
-            return None
+    def capture_screen(self):
+        """Capture Bambu Studio window or full screen"""
+        try:
+            with mss.mss() as sct:
+                if self.bambu_window and self.bambu_window.isActive:
+                    monitor = {
+                        "top": self.bambu_window.top,
+                        "left": self.bambu_window.left,
+                        "width": self.bambu_window.width,
+                        "height": self.bambu_window.height,
+                    }
+                else:
+                    monitor = sct.monitors[0]
+
+                sct_img = sct.grab(monitor)
+                img = np.array(sct_img)
+                img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
+                return img
+        except Exception as e:
+            print(f"Screenshot error: {e}")
+            return None
     
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
diff --git a/bambu_ai_assistant/chat_gui.py b/bambu_ai_assistant/chat_gui.py
index 7bd98b697d6b19fddd6b307de0b6b29ae64cb259..9899c2e64fe95fae773c3ddb3058c27da05efa2a 100644
--- a/bambu_ai_assistant/chat_gui.py
+++ b/bambu_ai_assistant/chat_gui.py
@@ -263,27 +272,39 @@ class BambuAIAssistant(ctk.CTk):
             
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
 
-if __name__ == "__main__":
-    app = BambuAIAssistant()
+if __name__ == "__main__":
+    import argparse
+
+    parser = argparse.ArgumentParser(description="Bambu AI Assistant")
+    parser.add_argument(
+        "--interval",
+        type=float,
+        default=CAPTURE_INTERVAL,
+        help="Screen capture interval in seconds",
+    )
+    args = parser.parse_args()
+
+    app = BambuAIAssistant(capture_interval=args.interval)
+    app.mainloop()
