REM Double-click this file to automatically install everything

@echo off
echo ========================================
echo   Bambu AI Assistant - Auto Installer
echo ========================================
echo.

echo [1/4] Installing Python packages...
pip install customtkinter>=5.2.0
pip install opencv-python>=4.8.0
pip install pyautogui>=0.9.54
pip install pygetwindow>=0.0.9
pip install Pillow>=10.0.0
pip install pytesseract>=0.3.10
pip install numpy>=1.24.0

echo.
echo [2/4] Checking Tesseract OCR...
where tesseract >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ Tesseract OCR found!
) else (
    echo ❌ Tesseract OCR not found!
    echo Please download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo Install to: C:\Program Files\Tesseract-OCR\
    echo Then add to Windows PATH
    pause
)

echo.
echo [3/4] Creating required folders...
if not exist "models" mkdir models
if not exist "outputs" mkdir outputs

echo.
echo [4/4] Testing installation...
python -c "import customtkinter, cv2, pyautogui, pytesseract; print('✅ All packages installed successfully!')" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ Installation successful!
    echo.
    echo You can now run: python chat_gui.py
) else (
    echo ❌ Some packages failed to install
    echo Please check the error messages above
)

echo.
echo Installation finished. Press any key to exit.
pause

