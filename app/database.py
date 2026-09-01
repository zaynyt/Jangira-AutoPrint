"""Database management for Jangira AutoPrint"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from contextlib import contextmanager
from app.config import DB_PATH, JobStatus
from app.logger import JangiraLogger

class DatabaseManager:
    """Manages SQLite database for print jobs and settings"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.logger = JangiraLogger.get_logger()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _initialize_database(self):
        """Create tables if they don't exist"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Jobs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    page_count INTEGER NOT NULL,
                    page_spec TEXT,
                    selected_pages TEXT,
                    copies INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    printer_name TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    started_at TIMESTAMP,
                    finished_at TIMESTAMP,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    UNIQUE(sha256, page_spec, copies)
                )
            ''')
            
            # Settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')
            
            # Printer state table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS printer_state (
                    id INTEGER PRIMARY KEY,
                    printer_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            ''')
            
            # Logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    job_id TEXT,
                    FOREIGN KEY (job_id) REFERENCES jobs(id)
                )
            ''')
            
            self.logger.info("Database initialized successfully")
    
    def create_job(self, job_id: str, file_path: str, file_name: str, 
                   sha256: str, page_count: int, page_spec: str, 
                   selected_pages: str, copies: int, printer_name: str) -> bool:
        """Create a new print job"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO jobs (
                        id, file_path, file_name, sha256, page_count,
                        page_spec, selected_pages, copies, status,
                        printer_name, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job_id, file_path, file_name, sha256, page_count,
                    page_spec, selected_pages, copies, JobStatus.PENDING,
                    printer_name, datetime.now()
                ))
                self.logger.info(f"Job created: {job_id}")
                return True
        except sqlite3.IntegrityError as e:
            self.logger.warning(f"Duplicate job detected: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error creating job: {e}")
            raise
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job details"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_pending_jobs(self) -> List[Dict]:
        """Get all pending jobs"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM jobs 
                WHERE status IN (?, ?)
                ORDER BY created_at ASC
            ''', (JobStatus.PENDING, JobStatus.RECOVERY_REQUIRED))
            return [dict(row) for row in cursor.fetchall()]
    
    def update_job_status(self, job_id: str, status: str, error_message: str = None):
        """Update job status"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if status == JobStatus.PRINTING:
                    cursor.execute('''
                        UPDATE jobs SET status = ?, started_at = ?
                        WHERE id = ?
                    ''', (status, datetime.now(), job_id))
                elif status in [JobStatus.PRINTED, JobStatus.PRINT_FAILED]:
                    cursor.execute('''
                        UPDATE jobs SET status = ?, finished_at = ?, error_message = ?
                        WHERE id = ?
                    ''', (status, datetime.now(), error_message, job_id))
                else:
                    cursor.execute('''
                        UPDATE jobs SET status = ?, error_message = ?
                        WHERE id = ?
                    ''', (status, error_message, job_id))
                self.logger.info(f"Job {job_id} status updated to {status}")
        except Exception as e:
            self.logger.error(f"Error updating job status: {e}")
            raise
    
    def increment_retry_count(self, job_id: str):
        """Increment retry count for a job"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE jobs SET retry_count = retry_count + 1
                WHERE id = ?
            ''', (job_id,))
    
    def get_job_by_hash(self, sha256: str, page_spec: str, copies: int) -> Optional[Dict]:
        """Check for duplicate jobs"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM jobs 
                WHERE sha256 = ? AND page_spec = ? AND copies = ?
                AND status NOT IN (?, ?)
                LIMIT 1
            ''', (sha256, page_spec, copies, JobStatus.PRINT_FAILED, JobStatus.CANCELLED))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def save_setting(self, key: str, value: str):
        """Save application setting"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value)
                VALUES (?, ?)
            ''', (key, value))
    
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get application setting"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            return row[0] if row else default
    
    def get_all_settings(self) -> Dict[str, str]:
        """Get all settings"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM settings')
            return {row[0]: row[1] for row in cursor.fetchall()}
    
    def get_job_history(self, status_filter: str = None, limit: int = 100) -> List[Dict]:
        """Get job history"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if status_filter:
                cursor.execute('''
                    SELECT * FROM jobs 
                    WHERE status = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (status_filter, limit))
            else:
                cursor.execute('''
                    SELECT * FROM jobs 
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def search_jobs(self, query: str) -> List[Dict]:
        """Search jobs by ID or filename"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            search_term = f"%{query}%"
            cursor.execute('''
                SELECT * FROM jobs 
                WHERE id LIKE ? OR file_name LIKE ?
                ORDER BY created_at DESC
            ''', (search_term, search_term))
            return [dict(row) for row in cursor.fetchall()]
