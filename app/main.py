"""Main Application Orchestrator - Jangira AutoPrint"""

import tkinter as tk
import threading
import time
from typing import Optional, Dict, List
from pathlib import Path
from app.config import (
    LOG_LEVEL, AUTO_PRINT, DEFAULT_PRINTER, QUEUE_POLL_INTERVAL,
    DATABASE_PATH, JobStatus
)
from app.logger import JangiraLogger
from app.database import DatabaseManager
from app.printer_manager import PrinterManager
from app.pdf_manager import PDFValidator, PDFProcessor
from app.job_executor import PrintJobExecutor, PrintJobQueue
from app.ui import PrintJobUI, SettingsDialog

class JangiraAutoprint:
    """Main application orchestrator"""
    
    def __init__(self):
        self.logger = JangiraLogger.get_logger()
        self.root: Optional[tk.Tk] = None
        self.ui: Optional[PrintJobUI] = None
        
        # Initialize core components
        self.db = DatabaseManager(str(DATABASE_PATH))
        self.printer_manager = PrinterManager()
        self.pdf_validator = PDFValidator()
        self.pdf_processor = PDFProcessor()
        self.job_executor = PrintJobExecutor(self.db, self.printer_manager)
        self.job_queue = PrintJobQueue(self.job_executor)
        
        # State
        self.is_running = False
        self.queue_thread: Optional[threading.Thread] = None
        
        self.logger.info("Jangira AutoPrint initialized")
    
    def start(self):
        """Start the application"""
        try:
            self.logger.info("Starting Jangira AutoPrint")
            
            # Initialize printer detection
            if not self.printer_manager.initialize():
                self.logger.warning("No printers detected on startup")
            
            # Initialize database
            if not self.db.initialize():
                self.logger.error("Failed to initialize database")
                return False
            
            # Create main window
            self.root = tk.Tk()
            self.ui = PrintJobUI(self.root, job_callback=self._handle_ui_callback)
            
            self.is_running = True
            
            # Start queue processing thread
            self._start_queue_processor()
            
            # Auto-print pending jobs if configured
            if AUTO_PRINT:
                self._auto_print_pending()
            
            # Refresh UI
            self.ui._refresh_printers()
            self.ui._refresh_job_history()
            
            self.logger.info("Application started successfully")
            
            # Run UI
            self.root.mainloop()
            
        except Exception as e:
            self.logger.error(f"Error starting application: {e}")
            return False
        
        finally:
            self.is_running = False
    
    def _start_queue_processor(self):
        """Start background queue processing thread"""
        self.queue_thread = threading.Thread(
            target=self._process_queue_loop,
            daemon=True
        )
        self.queue_thread.start()
        self.logger.debug("Queue processor thread started")
    
    def _process_queue_loop(self):
        """Background loop for processing print queue"""
        while self.is_running:
            try:
                # Process pending jobs
                self.job_queue.process_queue(
                    progress_callback=self._update_job_progress
                )
                
                # Wait before next poll
                time.sleep(QUEUE_POLL_INTERVAL)
            
            except Exception as e:
                self.logger.error(f"Error in queue processing loop: {e}")
                time.sleep(QUEUE_POLL_INTERVAL)
    
    def _handle_ui_callback(self, request: Dict) -> Dict:
        """Handle UI callbacks"""
        try:
            action = request.get("action")
            
            if action == "get_printers":
                return self._get_printers()
            
            elif action == "submit_job":
                return self._submit_print_job(request)
            
            elif action == "get_history":
                return self._get_job_history(request.get("limit", 10))
            
            elif action == "settings":
                return self._handle_settings()
            
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        
        except Exception as e:
            self.logger.error(f"Error handling UI callback: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_printers(self) -> List[str]:
        """Get available printers"""
        try:
            printers = self.printer_manager.get_available_printers()
            self.logger.debug(f"Available printers: {printers}")
            return printers
        except Exception as e:
            self.logger.error(f"Error getting printers: {e}")
            return []
    
    def _submit_print_job(self, request: Dict) -> Dict:
        """Submit a print job"""
        try:
            file_path = request.get("file_path")
            page_spec = request.get("page_spec", "")
            copies = request.get("copies", 1)
            printer_name = request.get("printer_name")
            
            if not file_path or not Path(file_path).exists():
                return {"success": False, "error": "File not found"}
            
            # Validate PDF
            is_valid, error = self.pdf_validator.validate_file(file_path)
            if not is_valid:
                return {"success": False, "error": error}
            
            # Process PDF
            is_valid, error, info = self.pdf_processor.process_pdf(file_path, page_spec)
            if not is_valid:
                return {"success": False, "error": error}
            
            # Submit job
            success, job_id = self.job_executor.submit_print_job(
                file_path=file_path,
                file_name=Path(file_path).name,
                page_spec=page_spec,
                copies=copies,
                printer_name=printer_name,
                sha256=info.get("sha256", ""),
                page_count=info.get("page_count", 0)
            )
            
            if success:
                self.logger.info(f"Print job submitted: {job_id}")
                return {"success": True, "job_id": job_id}
            else:
                return {"success": False, "error": job_id}
        
        except Exception as e:
            self.logger.error(f"Error submitting print job: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_job_history(self, limit: int = 10) -> List[Dict]:
        """Get job history"""
        try:
            jobs = self.db.get_jobs_by_status(None, limit=limit)
            return jobs if jobs else []
        except Exception as e:
            self.logger.error(f"Error getting job history: {e}")
            return []
    
    def _handle_settings(self) -> Dict:
        """Handle settings"""
        try:
            current_settings = {
                "default_printer": self.printer_manager.current_printer or "",
                "log_level": LOG_LEVEL,
                "auto_print": AUTO_PRINT
            }
            
            if self.root:
                def settings_callback(new_settings):
                    self.logger.info(f"Settings updated: {new_settings}")
                
                SettingsDialog(self.root, current_settings, settings_callback)
            
            return {"success": True}
        
        except Exception as e:
            self.logger.error(f"Error handling settings: {e}")
            return {"success": False, "error": str(e)}
    
    def _update_job_progress(self, progress_info: Dict):
        """Update job progress in UI"""
        try:
            job_id = progress_info.get("job_id")
            status = progress_info.get("status")
            
            if self.ui:
                self.ui.update_job_status(job_id, status)
            
            self.logger.debug(f"Job {job_id}: {status}")
        
        except Exception as e:
            self.logger.error(f"Error updating job progress: {e}")
    
    def _auto_print_pending(self):
        """Auto-print pending jobs on startup"""
        try:
            pending_jobs = self.db.get_pending_jobs()
            if pending_jobs:
                self.logger.info(f"Auto-printing {len(pending_jobs)} pending jobs")
                if self.ui:
                    self.ui.update_status(f"Auto-printing {len(pending_jobs)} pending jobs...")
        except Exception as e:
            self.logger.error(f"Error in auto-print: {e}")
    
    def stop(self):
        """Stop the application"""
        try:
            self.logger.info("Stopping application")
            self.is_running = False
            
            # Stop queue processor
            if self.queue_thread and self.queue_thread.is_alive():
                self.queue_thread.join(timeout=5)
            
            # Cleanup
            self.pdf_processor.manager.cleanup_temp_files()
            
            self.logger.info("Application stopped")
        
        except Exception as e:
            self.logger.error(f"Error stopping application: {e}")

class ApplicationManager:
    """Manages application lifecycle"""
    
    def __init__(self):
        self.app: Optional[JangiraAutoprint] = None
    
    def run(self):
        """Run the application"""
        try:
            self.app = JangiraAutoprint()
            self.app.start()
        except KeyboardInterrupt:
            print("\nShutting down...")
        except Exception as e:
            print(f"Fatal error: {e}")
        finally:
            if self.app:
                self.app.stop()

def main():
    """Main entry point"""
    manager = ApplicationManager()
    manager.run()

if __name__ == "__main__":
    main()
