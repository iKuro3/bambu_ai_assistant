# Bambu AI Assistant

Bambu AI Assistant adds a vision–enhanced chat helper to Bambu Studio. The assistant can analyze the screen, extract printing information and run slicer commands on your 3D models.

## Features

- **Chat interface** with commands processed by `slicer_control.py`.
- **Live screen capture** (via `mss`) and analysis in `chat_gui.py` and `realtime_helper.py`.
- Optional **advanced vision** tools in `advanced_vision.py`.
- Prebuilt **installation script** for Windows (`install_bambu_ai.bat`).

## Installation

Install Python dependencies with pip:

```bash
pip install -r bambu_ai_assistant/requirements.txt
```

On Windows you may also run `install_bambu_ai.bat` for an automated setup.

### Tesseract OCR

Tesseract is required for text recognition features. Install it separately and
ensure the `tesseract` executable is available in your system `PATH`. Official
installers and packages can be found on the [Tesseract GitHub
page](https://github.com/tesseract-ocr/tesseract).

## Usage

Launch the graphical assistant from the repository root. Use `--interval` to
adjust the delay between screen captures (default is one second):

```bash
python bambu_ai_assistant/chat_gui.py --interval 1
```

## API Setup

The chat interface streams responses from OpenAI's Chat Completion API. Set your
API key in the `OPENAI_API_KEY` environment variable before launching:

```bash
export OPENAI_API_KEY=sk-...
```

Optionally specify a different model with `OPENAI_MODEL`. The default is
`gpt-3.5-turbo`.

Example run after setting the key:

```bash
OPENAI_API_KEY=sk-... python bambu_ai_assistant/chat_gui.py --interval 1
```

## Folder Structure

```
├── README.md
└── bambu_ai_assistant
    ├── chat_gui.py          # main GUI application
    ├── realtime_helper.py   # screen analysis helpers
    ├── slicer_control.py    # slicer automation
    ├── advanced_vision.py   # extra vision features (optional)
    ├── requirements.txt     # Python dependencies
    └── install_bambu_ai.bat # Windows installer
```

The `models` and `outputs` folders are created automatically when running the installer or when processing models.
