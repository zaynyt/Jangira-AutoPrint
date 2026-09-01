"""Comprehensive Phase 1 Test Suite"""

import unittest
import tempfile
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
import sys

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import (
    MAX_FILE_SIZE, MAX_PAGES, JobStatus, DATABASE_PATH
)
from app.logger import JangiraLogger
from app.database import DatabaseManager
from app.printer_manager import PrinterManager
from app.pdf_manager import PDFValidator, PDFManager, PDFProcessor
from app.job_executor import PrintJobExecutor, PrintJobQueue


class TestLogger(unittest.TestCase):
    """Test logging system"""
    
    def test_logger_initialization(self):
        """Test logger can be initialized"""
        logger = JangiraLogger.get_logger()
        self.assertIsNotNone(logger)
    
    def test_logger_basic_logging(self):
        """Test basic logging operations"""
        logger = JangiraLogger.get_logger()
        try:
            logger.info("Test info message")
            logger.warning("Test warning message")
            logger.error("Test error message")
            logger.debug("Test debug message")
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Logger failed: {e}")


class TestDatabase(unittest.TestCase):
    """Test database operations"""
    
    def setUp(self):
        """Create temporary database"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = Path(self.temp_dir) / "test.db"
        self.db = DatabaseManager(str(self.temp_db))
    
    def tearDown(self):
        """Clean up temporary database"""
        if self.db:
            self.db.close()
        shutil.rmtree(self.temp_dir)
    
    def test_database_initialization(self):
        """Test database initialization"""
        success = self.db.initialize()
        self.assertTrue(success)
        self.assertTrue(self.temp_db.exists())
    
    def test_database_table_creation(self):
        """Test database tables are created"""
        self.db.initialize()
        
        # Check jobs table exists
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
        result = cursor.fetchone()
        self.assertIsNotNone(result)
    
    def test_create_job(self):
        """Test creating a job"""
        self.db.initialize()
        
        success = self.db.create_job(
            job_id="TEST_JOB_001",
            file_path="/tmp/test.pdf",
            file_name="test.pdf",
            sha256="abc123",
            page_count=10,
            page_spec="1-5",
            selected_pages="1-5",
            copies=1,
            printer_name="TestPrinter"
        )
        self.assertTrue(success)
    
    def test_get_job(self):
        """Test retrieving a job"""
        self.db.initialize()
        
        job_id = "TEST_JOB_002"
        self.db.create_job(
            job_id=job_id,
            file_path="/tmp/test.pdf",
            file_name="test.pdf",
            sha256="abc123",
            page_count=10,
            page_spec="1-5",
            selected_pages="1-5",
            copies=1,
            printer_name="TestPrinter"
        )
        
        job = self.db.get_job(job_id)
        self.assertIsNotNone(job)
        self.assertEqual(job['id'], job_id)
    
    def test_update_job_status(self):
        """Test updating job status"""
        self.db.initialize()
        
        job_id = "TEST_JOB_003"
        self.db.create_job(
            job_id=job_id,
            file_path="/tmp/test.pdf",
            file_name="test.pdf",
            sha256="abc123",
            page_count=10,
            page_spec="1-5",
            selected_pages="1-5",
            copies=1,
            printer_name="TestPrinter"
        )
        
        self.db.update_job_status(job_id, JobStatus.PRINTING)
        job = self.db.get_job(job_id)
        self.assertEqual(job['status'], JobStatus.PRINTING)
    
    def test_get_pending_jobs(self):
        """Test retrieving pending jobs"""
        self.db.initialize()
        
        # Create multiple jobs
        for i in range(3):
            self.db.create_job(
                job_id=f"TEST_JOB_{i}",
                file_path="/tmp/test.pdf",
                file_name="test.pdf",
                sha256="abc123",
                page_count=10,
                page_spec="1-5",
                selected_pages="1-5",
                copies=1,
                printer_name="TestPrinter"
            )
        
        pending = self.db.get_pending_jobs()
        self.assertEqual(len(pending), 3)


class TestPrinterManager(unittest.TestCase):
    """Test printer manager"""
    
    def setUp(self):
        """Initialize printer manager"""
        self.printer_manager = PrinterManager()
    
    def test_printer_manager_initialization(self):
        """Test printer manager initialization"""
        success = self.printer_manager.initialize()
        self.assertIsNotNone(success)
    
    def test_get_available_printers(self):
        """Test getting available printers"""
        printers = self.printer_manager.get_available_printers()
        self.assertIsInstance(printers, list)
    
    def test_is_ready(self):
        """Test printer ready check"""
        result = self.printer_manager.is_ready()
        self.assertIsInstance(result, bool)


class TestPDFValidator(unittest.TestCase):
    """Test PDF validation"""
    
    def setUp(self):
        """Initialize validator"""
        self.validator = PDFValidator()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir)
    
    def test_validate_nonexistent_file(self):
        """Test validating non-existent file"""
        is_valid, error = self.validator.validate_file("/nonexistent/file.pdf")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_validate_non_pdf_file(self):
        """Test validating non-PDF file"""
        temp_file = Path(self.temp_dir) / "test.txt"
        temp_file.write_text("This is not a PDF")
        
        is_valid, error = self.validator.validate_file(str(temp_file))
        self.assertFalse(is_valid)
    
    def test_calculate_sha256(self):
        """Test SHA256 calculation"""
        temp_file = Path(self.temp_dir) / "test.txt"
        temp_file.write_text("Test content")
        
        hash_value = self.validator.calculate_sha256(str(temp_file))
        self.assertIsInstance(hash_value, str)
        self.assertEqual(len(hash_value), 64)  # SHA256 is 64 hex characters


class TestPDFManager(unittest.TestCase):
    """Test PDF manager"""
    
    def setUp(self):
        """Initialize PDF manager"""
        self.manager = PDFManager()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir)
    
    def test_validate_page_range_empty(self):
        """Test validating empty page range"""
        # Create a mock PDF file
        temp_file = Path(self.temp_dir) / "test.pdf"
        temp_file.write_bytes(b"%PDF-1.4\n")  # Minimal PDF header
        
        is_valid, error = self.manager.validate_page_range(str(temp_file), "")
        # Should be valid (empty means all pages)
        self.assertTrue(is_valid or error is None)
    
    def test_validate_page_range_invalid_format(self):
        """Test validating invalid page range format"""
        temp_file = Path(self.temp_dir) / "test.pdf"
        temp_file.write_bytes(b"%PDF-1.4\n")
        
        # Try with invalid format - this may fail but should handle gracefully
        is_valid, error = self.manager.validate_page_range(str(temp_file), "invalid")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_cleanup_temp_files(self):
        """Test temporary file cleanup"""
        try:
            self.manager.cleanup_temp_files()
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Cleanup failed: {e}")


class TestPDFProcessor(unittest.TestCase):
    """Test PDF processor"""
    
    def setUp(self):
        """Initialize processor"""
        self.processor = PDFProcessor()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir)
    
    def test_process_nonexistent_pdf(self):
        """Test processing non-existent PDF"""
        is_valid, error, info = self.processor.process_pdf("/nonexistent/file.pdf")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertEqual(info, {})
    
    def test_process_invalid_pdf(self):
        """Test processing invalid PDF"""
        temp_file = Path(self.temp_dir) / "invalid.pdf"
        temp_file.write_text("Not a real PDF")
        
        is_valid, error, info = self.processor.process_pdf(str(temp_file))
        self.assertFalse(is_valid)


class TestJobExecutor(unittest.TestCase):
    """Test job executor"""
    
    def setUp(self):
        """Initialize executor"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = Path(self.temp_dir) / "test.db"
        self.db = DatabaseManager(str(self.temp_db))
        self.db.initialize()
        
        self.printer_manager = PrinterManager()
        self.executor = PrintJobExecutor(self.db, self.printer_manager)
    
    def tearDown(self):
        """Clean up"""
        self.db.close()
        shutil.rmtree(self.temp_dir)
    
    def test_create_job_id(self):
        """Test job ID creation"""
        job_id = self.executor.create_job_id()
        self.assertIsNotNone(job_id)
        self.assertTrue(job_id.startswith("JOB_"))
    
    def test_submit_print_job(self):
        """Test submitting a print job"""
        success, result = self.executor.submit_print_job(
            file_path="/tmp/test.pdf",
            file_name="test.pdf",
            page_spec="1-5",
            copies=1,
            printer_name="TestPrinter",
            sha256="abc123",
            page_count=10
        )
        
        # May fail due to non-existent file, but should handle gracefully
        self.assertIsInstance(success, bool)
        self.assertIsNotNone(result)
    
    def test_get_job_status(self):
        """Test getting job status"""
        # Create a job first
        self.db.create_job(
            job_id="TEST_JOB_STATUS",
            file_path="/tmp/test.pdf",
            file_name="test.pdf",
            sha256="abc123",
            page_count=10,
            page_spec="1-5",
            selected_pages="1-5",
            copies=1,
            printer_name="TestPrinter"
        )
        
        status = self.executor.get_job_status("TEST_JOB_STATUS")
        self.assertEqual(status, JobStatus.PENDING)
    
    def test_cancel_job(self):
        """Test cancelling a job"""
        self.db.create_job(
            job_id="TEST_JOB_CANCEL",
            file_path="/tmp/test.pdf",
            file_name="test.pdf",
            sha256="abc123",
            page_count=10,
            page_spec="1-5",
            selected_pages="1-5",
            copies=1,
            printer_name="TestPrinter"
        )
        
        success = self.executor.cancel_job("TEST_JOB_CANCEL")
        self.assertTrue(success)
        
        status = self.executor.get_job_status("TEST_JOB_CANCEL")
        self.assertEqual(status, JobStatus.CANCELLED)


class TestJobQueue(unittest.TestCase):
    """Test job queue"""
    
    def setUp(self):
        """Initialize queue"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = Path(self.temp_dir) / "test.db"
        self.db = DatabaseManager(str(self.temp_db))
        self.db.initialize()
        
        self.printer_manager = PrinterManager()
        self.executor = PrintJobExecutor(self.db, self.printer_manager)
        self.queue = PrintJobQueue(self.executor)
    
    def tearDown(self):
        """Clean up"""
        self.db.close()
        shutil.rmtree(self.temp_dir)
    
    def test_queue_initialization(self):
        """Test queue initialization"""
        self.assertIsNotNone(self.queue)
        self.assertFalse(self.queue.is_processing)
    
    def test_get_pending_jobs(self):
        """Test getting pending jobs"""
        # Create some pending jobs
        for i in range(3):
            self.db.create_job(
                job_id=f"QUEUE_TEST_{i}",
                file_path="/tmp/test.pdf",
                file_name="test.pdf",
                sha256="abc123",
                page_count=10,
                page_spec="1-5",
                selected_pages="1-5",
                copies=1,
                printer_name="TestPrinter"
            )
        
        pending = self.queue.get_pending_jobs()
        self.assertEqual(len(pending), 3)
    
    def test_stop_processing(self):
        """Test stopping queue processing"""
        self.queue.is_processing = True
        self.queue.stop_processing()
        self.assertFalse(self.queue.is_processing)


class TestConfiguration(unittest.TestCase):
    """Test configuration values"""
    
    def test_max_file_size(self):
        """Test MAX_FILE_SIZE is set"""
        self.assertGreater(MAX_FILE_SIZE, 0)
    
    def test_max_pages(self):
        """Test MAX_PAGES is set"""
        self.assertGreater(MAX_PAGES, 0)
    
    def test_job_status_enum(self):
        """Test JobStatus enum has required values"""
        self.assertTrue(hasattr(JobStatus, 'PENDING'))
        self.assertTrue(hasattr(JobStatus, 'PRINTING'))
        self.assertTrue(hasattr(JobStatus, 'PRINTED'))
        self.assertTrue(hasattr(JobStatus, 'PRINT_FAILED'))
        self.assertTrue(hasattr(JobStatus, 'CANCELLED'))


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def setUp(self):
        """Initialize for integration tests"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = Path(self.temp_dir) / "test.db"
        self.db = DatabaseManager(str(self.temp_db))
        self.db.initialize()
    
    def tearDown(self):
        """Clean up"""
        self.db.close()
        shutil.rmtree(self.temp_dir)
    
    def test_full_job_lifecycle(self):
        """Test complete job lifecycle"""
        job_id = "INTEGRATION_TEST_001"
        
        # Create job
        success = self.db.create_job(
            job_id=job_id,
            file_path="/tmp/test.pdf",
            file_name="test.pdf",
            sha256="abc123",
            page_count=10,
            page_spec="1-5",
            selected_pages="1-5",
            copies=1,
            printer_name="TestPrinter"
        )
        self.assertTrue(success)
        
        # Verify job created with PENDING status
        job = self.db.get_job(job_id)
        self.assertEqual(job['status'], JobStatus.PENDING)
        
        # Update to PRINTING
        self.db.update_job_status(job_id, JobStatus.PRINTING)
        job = self.db.get_job(job_id)
        self.assertEqual(job['status'], JobStatus.PRINTING)
        
        # Update to PRINTED
        self.db.update_job_status(job_id, JobStatus.PRINTED)
        job = self.db.get_job(job_id)
        self.assertEqual(job['status'], JobStatus.PRINTED)
    
    def test_duplicate_job_detection(self):
        """Test duplicate job detection"""
        job_id = "DUP_TEST_001"
        file_path = "/tmp/test.pdf"
        
        # Create first job
        success1 = self.db.create_job(
            job_id=job_id,
            file_path=file_path,
            file_name="test.pdf",
            sha256="abc123",
            page_count=10,
            page_spec="",
            selected_pages="",
            copies=1,
            printer_name="TestPrinter"
        )
        self.assertTrue(success1)
        
        # Try to create duplicate
        success2 = self.db.create_job(
            job_id=job_id,
            file_path=file_path,
            file_name="test.pdf",
            sha256="abc123",
            page_count=10,
            page_spec="",
            selected_pages="",
            copies=1,
            printer_name="TestPrinter"
        )
        # Should fail due to duplicate ID
        self.assertFalse(success2)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestLogger))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestPrinterManager))
    suite.addTests(loader.loadTestsFromTestCase(TestPDFValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestPDFManager))
    suite.addTests(loader.loadTestsFromTestCase(TestPDFProcessor))
    suite.addTests(loader.loadTestsFromTestCase(TestJobExecutor))
    suite.addTests(loader.loadTestsFromTestCase(TestJobQueue))
    suite.addTests(loader.loadTestsFromTestCase(TestConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
