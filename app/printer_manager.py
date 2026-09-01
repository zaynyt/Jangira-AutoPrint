"""Windows Printer Manager - Real printer detection and control"""

import subprocess
import json
from typing import List, Optional, Dict
from app.config import PrinterStatus, DEFAULT_PRINTER
from app.logger import JangiraLogger

class WindowsPrinterAdapter:
    """Adapter for Windows printer APIs using pywin32 and WMI"""
    
    def __init__(self):
        self.logger = JangiraLogger.get_logger()
        self._printers_cache = {}
        self._default_printer = None
    
    def detect_printers(self) -> List[str]:
        """Detect all installed Windows printers"""
        try:
            import win32print
            printers = []
            
            # Get all printers
            enum_flags = win32print.PRINTER_ENUM_LOCAL
            level = 4
            
            try:
                printer_info = win32print.EnumPrinters(enum_flags, None, level)
                for printer in printer_info:
                    printer_name = printer['pPrinterName']
                    printers.append(printer_name)
                    self.logger.debug(f"Detected printer: {printer_name}")
            except Exception as e:
                self.logger.warning(f"Error enumerating printers: {e}")
            
            self._printers_cache = {name: name for name in printers}
            return printers
        except ImportError:
            self.logger.error("pywin32 not installed. Cannot detect printers.")
            return []
        except Exception as e:
            self.logger.error(f"Error detecting printers: {e}")
            return []
    
    def get_default_printer(self) -> Optional[str]:
        """Get the default Windows printer"""
        try:
            import win32print
            default = win32print.GetDefaultPrinter()
            self._default_printer = default
            self.logger.info(f"Default printer: {default}")
            return default
        except Exception as e:
            self.logger.warning(f"Could not get default printer: {e}")
            return None
    
    def get_printer_status(self, printer_name: str) -> str:
        """Get status of a specific printer"""
        try:
            import win32print
            import win32con
            
            printer_handle = None
            try:
                printer_handle = win32print.OpenPrinter(printer_name)
            except:
                return PrinterStatus.OFFLINE
            
            if printer_handle is None:
                return PrinterStatus.OFFLINE
            
            try:
                status_info = win32print.GetPrinter(printer_handle, 2)
                status = status_info.get('Status', 0)
                
                # Parse Windows printer status flags
                if status == 0:
                    return PrinterStatus.READY
                elif status & 0x00000010:  # PRINTER_STATUS_PAUSED
                    return PrinterStatus.PAUSED
                elif status & 0x00000001:  # PRINTER_STATUS_BUSY
                    return PrinterStatus.PRINTING
                elif status & 0x00000004:  # PRINTER_STATUS_ERROR
                    return PrinterStatus.ERROR
                elif status & 0x00000008:  # PRINTER_STATUS_PAPER_JAM
                    return PrinterStatus.ERROR
                elif status & 0x00000100:  # PRINTER_STATUS_PAPER_OUT
                    return PrinterStatus.ERROR
                else:
                    return PrinterStatus.UNKNOWN
            finally:
                win32print.ClosePrinter(printer_handle)
        except ImportError:
            self.logger.error("pywin32 not available")
            return PrinterStatus.UNKNOWN
        except Exception as e:
            self.logger.error(f"Error getting printer status for {printer_name}: {e}")
            return PrinterStatus.ERROR
    
    def is_printer_available(self, printer_name: str) -> bool:
        """Check if printer is available"""
        status = self.get_printer_status(printer_name)
        return status in [PrinterStatus.READY, PrinterStatus.PRINTING]
    
    def find_preferred_printer(self) -> Optional[str]:
        """Find the preferred Brother printer"""
        printers = self.detect_printers()
        
        # Look for exact match
        for printer in printers:
            if DEFAULT_PRINTER in printer or printer == DEFAULT_PRINTER:
                self.logger.info(f"Found preferred printer: {printer}")
                return printer
        
        # Look for partial match
        for printer in printers:
            if "Brother" in printer or "DCP" in printer or "L2520" in printer:
                self.logger.info(f"Found Brother printer: {printer}")
                return printer
        
        # Return default if available
        default = self.get_default_printer()
        if default:
            return default
        
        # Return first printer
        return printers[0] if printers else None
    
    def refresh_printer_status(self, printer_name: str) -> Dict[str, str]:
        """Refresh and return printer information"""
        status = self.get_printer_status(printer_name)
        return {
            "name": printer_name,
            "status": status,
            "available": status in [PrinterStatus.READY, PrinterStatus.PRINTING]
        }

class PrinterManager:
    """High-level printer management"""
    
    def __init__(self):
        self.adapter = WindowsPrinterAdapter()
        self.logger = JangiraLogger.get_logger()
        self.current_printer: Optional[str] = None
        self.current_status: str = PrinterStatus.UNKNOWN
    
    def initialize(self) -> bool:
        """Initialize printer detection"""
        try:
            printers = self.adapter.detect_printers()
            if not printers:
                self.logger.warning("No printers detected")
                return False
            
            # Try to find preferred printer
            preferred = self.adapter.find_preferred_printer()
            if preferred:
                self.current_printer = preferred
                self.current_status = self.adapter.get_printer_status(preferred)
                self.logger.info(f"Using printer: {preferred}, Status: {self.current_status}")
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Error initializing printer manager: {e}")
            return False
    
    def get_available_printers(self) -> List[str]:
        """Get list of available printers"""
        return self.adapter.detect_printers()
    
    def select_printer(self, printer_name: str) -> bool:
        """Select a specific printer"""
        try:
            printers = self.adapter.detect_printers()
            if printer_name not in printers:
                self.logger.error(f"Printer not found: {printer_name}")
                return False
            
            self.current_printer = printer_name
            self.current_status = self.adapter.get_printer_status(printer_name)
            self.logger.info(f"Selected printer: {printer_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error selecting printer: {e}")
            return False
    
    def get_current_printer(self) -> Optional[str]:
        """Get currently selected printer"""
        return self.current_printer
    
    def get_status(self) -> str:
        """Get current printer status"""
        if self.current_printer:
            self.current_status = self.adapter.get_printer_status(self.current_printer)
        return self.current_status
    
    def is_ready(self) -> bool:
        """Check if printer is ready"""
        status = self.get_status()
        return status == PrinterStatus.READY
    
    def refresh_status(self) -> Dict[str, str]:
        """Refresh printer status"""
        if not self.current_printer:
            return {"status": PrinterStatus.UNKNOWN, "available": False}
        return self.adapter.refresh_printer_status(self.current_printer)
