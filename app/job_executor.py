"""Print Job Execution Engine"""

import subprocess
import time
import uuid
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime
from app.config import JobStatus, PRINT_TIMEOUT, JOB_RETRY_LIMIT
from app.logger import JangiraLogger
from app.database import DatabaseManager
from app.printer_manager import PrinterManager
from app.pdf_manager import PDFManager

class PrintJobExecutor:
    """Executes print jobs with error handling and recovery"""
    
    def __init__(self, db_manager: DatabaseManager, printer_manager: PrinterManager):
        self.db = db_manager
        self.printer_manager = printer_manager
        self.pdf_manager = PDFManager()
        self.logger = JangiraLogger.get_logger()
        self.current_job_id: Optional[str] = None
        self.current_job_process: Optional[subprocess.Popen] = None
    
    def create_job_id(self) -> str:
        """Generate unique job ID"""
        return f"JOB_{uuid.uuid4().hex[:12].upper()}_{int(time.time())}"
    
    def submit_print_job(self, file_path: str, file_name: str, page_spec: str,
                        copies: int, printer_name: str, sha256: str, 
                        page_count: int) -> tuple[bool, str]:
        """Submit a new print job"""
        try:
            job_id = self.create_job_id()
            
            # Create job in database
            success = self.db.create_job(
                job_id=job_id,
                file_path=file_path,
                file_name=file_name,
                sha256=sha256,
                page_count=page_count,
                page_spec=page_spec,
                selected_pages=page_spec,
                copies=copies,
                printer_name=printer_name
            )
            
            if not success:
                return False, "Duplicate job detected - file already queued"
            
            self.logger.info(f"Job submitted: {job_id} - {file_name}")
            return True, job_id
        except Exception as e:
            self.logger.error(f"Error submitting print job: {e}")
            return False, str(e)
    
    def execute_job(self, job_id: str, progress_callback: Optional[Callable] = None) -> bool:
        """Execute a print job"""
        try:
            self.current_job_id = job_id
            
            # Get job details
            job = self.db.get_job(job_id)
            if not job:
                self.logger.error(f"Job not found: {job_id}")
                return False
            
            file_path = job['file_path']
            printer_name = job['printer_name']
            copies = job['copies']
            page_spec = job['page_spec']
            
            # Update status to printing
            self.db.update_job_status(job_id, JobStatus.PRINTING)
            if progress_callback:
                progress_callback({"status": JobStatus.PRINTING, "job_id": job_id})
            
            # Check printer is ready
            if not self.printer_manager.is_ready():
                raise Exception(f"Printer '{printer_name}' is not ready")
            
            # Get printable file (extract pages if needed)
            printable_path, is_temp = self.pdf_manager.get_printable_path(file_path, page_spec)
            
            try:
                # Send to printer using Windows print command
                success = self._send_to_printer(printable_path, printer_name, copies)
                
                if success:
                    self.db.update_job_status(job_id, JobStatus.PRINTED)
                    self.logger.info(f"Job printed successfully: {job_id}")
                    if progress_callback:
                        progress_callback({"status": JobStatus.PRINTED, "job_id": job_id})
                    return True
                else:
                    raise Exception("Print command failed")
            finally:
                # Clean up temp file if created
                if is_temp:
                    try:
                        Path(printable_path).unlink()
                    except:
                        pass
        
        except Exception as e:
            self.logger.error(f"Error executing job {job_id}: {e}")
            
            # Handle retry
            job = self.db.get_job(job_id)
            if job and job['retry_count'] < JOB_RETRY_LIMIT:
                self.db.increment_retry_count(job_id)
                self.db.update_job_status(job_id, JobStatus.RECOVERY_REQUIRED, str(e))
                if progress_callback:
                    progress_callback({
                        "status": JobStatus.RECOVERY_REQUIRED,
                        "job_id": job_id,
                        "error": str(e),
                        "retry_count": job['retry_count'] + 1
                    })
                return False
            else:
                # Max retries reached
                self.db.update_job_status(job_id, JobStatus.PRINT_FAILED, str(e))
                if progress_callback:
                    progress_callback({
                        "status": JobStatus.PRINT_FAILED,
                        "job_id": job_id,
                        "error": str(e)
                    })
                return False
        
        finally:
            self.current_job_id = None
            self.current_job_process = None
    
    def _send_to_printer(self, file_path: str, printer_name: str, copies: int) -> bool:
        """Send file to printer using Windows print command"""
        try:
            # Use Windows print command
            cmd = [
                'powershell',
                '-Command',
                f'$print_queue = New-Object System.Printing.PrintQueue($null, "{printer_name}");'
                f'$print_queue.AddJob("Jangira Print", "{file_path}", $false);'
                f'Start-Sleep -Seconds 2'
            ]
            
            self.logger.debug(f"Executing print command for {printer_name}")
            
            # Execute print command
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=PRINT_TIMEOUT
            )
            self.current_job_process = process
            
            stdout, stderr = process.communicate(timeout=PRINT_TIMEOUT)
            
            if process.returncode != 0:
                self.logger.error(f"Print command failed: {stderr.decode()}")
                return False
            
            self.logger.info(f"Print job sent to {printer_name}")
            return True
        
        except subprocess.TimeoutExpired:
            if self.current_job_process:
                self.current_job_process.kill()
            self.logger.error(f"Print command timeout after {PRINT_TIMEOUT}s")
            return False
        except Exception as e:
            self.logger.error(f"Error sending to printer: {e}")
            return False
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or running job"""
        try:
            job = self.db.get_job(job_id)
            if not job:
                return False
            
            # If currently executing, kill process
            if self.current_job_id == job_id and self.current_job_process:
                self.current_job_process.kill()
            
            self.db.update_job_status(job_id, JobStatus.CANCELLED)
            self.logger.info(f"Job cancelled: {job_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error cancelling job: {e}")
            return False
    
    def get_job_status(self, job_id: str) -> Optional[str]:
        """Get current job status"""
        try:
            job = self.db.get_job(job_id)
            return job['status'] if job else None
        except Exception as e:
            self.logger.error(f"Error getting job status: {e}")
            return None
    
    def retry_job(self, job_id: str) -> bool:
        """Retry a failed job"""
        try:
            job = self.db.get_job(job_id)
            if not job:
                return False
            
            # Reset retry count and status
            self.db.update_job_status(job_id, JobStatus.PENDING)
            
            self.logger.info(f"Job queued for retry: {job_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error retrying job: {e}")
            return False

class PrintJobQueue:
    """Manages the print job queue"""
    
    def __init__(self, executor: PrintJobExecutor):
        self.executor = executor
        self.db = executor.db
        self.logger = JangiraLogger.get_logger()
        self.is_processing = False
    
    def get_pending_jobs(self) -> list:
        """Get all pending jobs"""
        return self.db.get_pending_jobs()
    
    def process_queue(self, progress_callback: Optional[Callable] = None) -> int:
        """Process all pending jobs"""
        jobs_processed = 0
        
        try:
            self.is_processing = True
            pending_jobs = self.get_pending_jobs()
            
            self.logger.info(f"Processing {len(pending_jobs)} pending jobs")
            
            for job in pending_jobs:
                if not self.is_processing:
                    break
                
                success = self.executor.execute_job(job['id'], progress_callback)
                if success:
                    jobs_processed += 1
                
                # Small delay between jobs
                time.sleep(1)
            
            self.logger.info(f"Queue processing complete: {jobs_processed} jobs printed")
            return jobs_processed
        
        except Exception as e:
            self.logger.error(f"Error processing queue: {e}")
            return jobs_processed
        
        finally:
            self.is_processing = False
    
    def stop_processing(self):
        """Stop queue processing"""
        self.is_processing = False
        self.logger.info("Queue processing stopped")
