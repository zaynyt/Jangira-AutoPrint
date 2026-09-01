"""Jangira AutoPrint Test Suite"""

__version__ = "1.0.0"
__author__ = "Jangira Development Team"

from tests.test_phase1 import (
    TestLogger,
    TestDatabase,
    TestPrinterManager,
    TestPDFValidator,
    TestPDFManager,
    TestPDFProcessor,
    TestJobExecutor,
    TestJobQueue,
    TestConfiguration,
    TestIntegration,
    run_tests
)

__all__ = [
    "TestLogger",
    "TestDatabase",
    "TestPrinterManager",
    "TestPDFValidator",
    "TestPDFManager",
    "TestPDFProcessor",
    "TestJobExecutor",
    "TestJobQueue",
    "TestConfiguration",
    "TestIntegration",
    "run_tests"
]
