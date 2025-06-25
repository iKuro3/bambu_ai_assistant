# Bambu AI Assistant

A simple assistant for Bambu Studio that combines computer vision with convenient GUI controls. The project provides:

- **Live screen capture** of the Bambu Studio window with basic analysis.
- **Chat-based control** where you can ask questions or issue slicing commands.
- **Model manipulation** utilities such as scale, rotate and material changes (see `slicer_control.py`).
- Optional helper modules for more advanced vision features.

## Installation

Use Python 3.8+ and install the dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the main GUI and make sure Bambu Studio is open:

```bash
python bambu_ai_assistant/chat_gui.py
```

Toggle **Live Vision** to start capturing the window. You can then chat with the assistant to perform actions like slicing or printing.
