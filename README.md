# Jangira AutoPrint

**Cyber Cafe Automatic Printing System**

A professional Windows desktop application for automated PDF printing on Brother DCP-L2520D series printers.

## Phase 1: Local Windows Real Printer Agent

### Target Environment
- Windows 10 Pro, 64-bit
- Brother DCP-L2520D series (USB connected)
- Black & White laser printer
- A4 paper
- Windows Print System with Brother driver

### Key Features
- ✅ Real Windows printer detection and integration
- ✅ Live printer status monitoring
- ✅ PDF page selection and copies
- ✅ Persistent local SQLite queue
- ✅ Duplicate print protection
- ✅ Crash recovery
- ✅ Professional PySide6 UI
- ✅ System tray integration
- ✅ Comprehensive logging
- ✅ Windows installer/uninstaller

### Tech Stack
- Python 3.11+
- PySide6 (Qt for Python)
- SQLite3
- PyMuPDF (fitz)
- pywin32 (Windows integration)
- PyInstaller (EXE packaging)

### Project Structure
```
JangiraAutoPrint/
├── main.py
├── requirements.txt
├── README.md
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── printer_manager.py
│   ├── print_engine.py
│   ├── print_queue.py
│   ├── pdf_manager.py
│   ├── job_manager.py
│   ├── recovery.py
│   ├── logger.py
│   └── ui/
│       ├── main_window.py
│       ├── dashboard.py
│       ├── queue_view.py
│       ├── printer_view.py
│       ├── history_view.py
│       ├── settings_view.py
│       └── components/
├── assets/
│   └── icon.ico
├── scripts/
│   ├── build_exe.bat
│   └── build_installer.bat
└── installer/
```

## Installation & Development

### Prerequisites
```bash
Python 3.11+
pip
```

### Setup
```bash
git clone https://github.com/zaynyt/Jangira-AutoPrint.git
cd Jangira-AutoPrint
pip install -r requirements.txt
python main.py
```

### Build Executable
```bash
cd scripts
build_exe.bat
```

### Build Installer
```bash
cd scripts
build_installer.bat
```

## Status
🚧 **Phase 1 In Progress**: Building complete Windows printer integration and local printing system.

---
**Author:** zaynyt  
**License:** Proprietary
