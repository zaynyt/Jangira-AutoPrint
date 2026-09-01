# Phase 1 Testing Guide

## Quick Start

### Run All Tests
```bash
python -m unittest tests.test_phase1 -v
```

### Run Specific Test Class
```bash
python -m unittest tests.test_phase1.TestDatabase -v
```

### Run Specific Test
```bash
python -m unittest tests.test_phase1.TestDatabase.test_create_job -v
```

## Test Coverage

### 1. **Logger Tests** (2 tests)
Tests the structured logging system.

```bash
python -m unittest tests.test_phase1.TestLogger -v
```

**Tests:**
- `test_logger_initialization` - Verify logger can be created
- `test_logger_basic_logging` - Verify logging operations work

**Expected Results:** ✅ 2/2 PASS

---

### 2. **Database Tests** (6 tests)
Tests SQLite database operations and job persistence.

```bash
python -m unittest tests.test_phase1.TestDatabase -v
```

**Tests:**
- `test_database_initialization` - Verify database file is created
- `test_database_table_creation` - Verify jobs table exists
- `test_create_job` - Verify job creation works
- `test_get_job` - Verify job retrieval works
- `test_update_job_status` - Verify status updates work
- `test_get_pending_jobs` - Verify pending jobs query works

**Expected Results:** ✅ 6/6 PASS

---

### 3. **Printer Manager Tests** (3 tests)
Tests Windows printer detection and management.

```bash
python -m unittest tests.test_phase1.TestPrinterManager -v
```

**Tests:**
- `test_printer_manager_initialization` - Verify printer manager initializes
- `test_get_available_printers` - Verify printer detection returns list
- `test_is_ready` - Verify printer ready check works

**Expected Results:** ✅ 3/3 PASS
**Note:** Results depend on system printer configuration

---

### 4. **PDF Validator Tests** (3 tests)
Tests PDF file validation and hashing.

```bash
python -m unittest tests.test_phase1.TestPDFValidator -v
```

**Tests:**
- `test_validate_nonexistent_file` - Verify non-existent files are rejected
- `test_validate_non_pdf_file` - Verify non-PDF files are rejected
- `test_calculate_sha256` - Verify SHA256 hashing works correctly

**Expected Results:** ✅ 3/3 PASS

---

### 5. **PDF Manager Tests** (3 tests)
Tests PDF page management and temporary file handling.

```bash
python -m unittest tests.test_phase1.TestPDFManager -v
```

**Tests:**
- `test_validate_page_range_empty` - Verify empty page spec is valid
- `test_validate_page_range_invalid_format` - Verify invalid formats are rejected
- `test_cleanup_temp_files` - Verify temporary files can be cleaned up

**Expected Results:** ✅ 3/3 PASS

---

### 6. **PDF Processor Tests** (2 tests)
Tests high-level PDF processing operations.

```bash
python -m unittest tests.test_phase1.TestPDFProcessor -v
```

**Tests:**
- `test_process_nonexistent_pdf` - Verify non-existent PDFs are rejected
- `test_process_invalid_pdf` - Verify invalid PDFs are rejected

**Expected Results:** ✅ 2/2 PASS

---

### 7. **Job Executor Tests** (4 tests)
Tests print job submission and execution.

```bash
python -m unittest tests.test_phase1.TestJobExecutor -v
```

**Tests:**
- `test_create_job_id` - Verify unique job IDs are generated
- `test_submit_print_job` - Verify job submission works
- `test_get_job_status` - Verify job status retrieval works
- `test_cancel_job` - Verify job cancellation works

**Expected Results:** ✅ 4/4 PASS

---

### 8. **Job Queue Tests** (3 tests)
Tests print job queue management.

```bash
python -m unittest tests.test_phase1.TestJobQueue -v
```

**Tests:**
- `test_queue_initialization` - Verify queue initializes correctly
- `test_get_pending_jobs` - Verify pending jobs retrieval works
- `test_stop_processing` - Verify queue can be stopped

**Expected Results:** ✅ 3/3 PASS

---

### 9. **Configuration Tests** (3 tests)
Tests configuration values and enums.

```bash
python -m unittest tests.test_phase1.TestConfiguration -v
```

**Tests:**
- `test_max_file_size` - Verify MAX_FILE_SIZE is set
- `test_max_pages` - Verify MAX_PAGES is set
- `test_job_status_enum` - Verify JobStatus enum has all required values

**Expected Results:** ✅ 3/3 PASS

---

### 10. **Integration Tests** (2 tests)
Tests complete workflows and interactions between components.

```bash
python -m unittest tests.test_phase1.TestIntegration -v
```

**Tests:**
- `test_full_job_lifecycle` - Verify complete job lifecycle (PENDING → PRINTING → PRINTED)
- `test_duplicate_job_detection` - Verify duplicate jobs are rejected

**Expected Results:** ✅ 2/2 PASS

---

## Full Test Summary

**Total Tests:** 31
**Categories:** 10

| Category | Tests | Expected |
|----------|-------|----------|
| Logger | 2 | ✅ 2/2 PASS |
| Database | 6 | ✅ 6/6 PASS |
| Printer Manager | 3 | ✅ 3/3 PASS |
| PDF Validator | 3 | ✅ 3/3 PASS |
| PDF Manager | 3 | ✅ 3/3 PASS |
| PDF Processor | 2 | ✅ 2/2 PASS |
| Job Executor | 4 | ✅ 4/4 PASS |
| Job Queue | 3 | ✅ 3/3 PASS |
| Configuration | 3 | ✅ 3/3 PASS |
| Integration | 2 | ✅ 2/2 PASS |
| **TOTAL** | **31** | **✅ 31/31 PASS** |

---

## Running Tests

### Option 1: Run All Tests
```bash
python tests/test_phase1.py
```

### Option 2: Use unittest
```bash
python -m unittest tests.test_phase1 -v
```

### Option 3: Run Specific Test Category
```bash
# Run only database tests
python -m unittest tests.test_phase1.TestDatabase -v

# Run only integration tests
python -m unittest tests.test_phase1.TestIntegration -v
```

### Option 4: Verbose Output
```bash
python -m unittest tests.test_phase1 -v 2>&1 | tee test_results.log
```

---

## Interpreting Results

### Success Output
```
test_calculate_sha256 (tests.test_phase1.TestPDFValidator) ... ok
test_create_job (tests.test_phase1.TestDatabase) ... ok
test_database_initialization (tests.test_phase1.TestDatabase) ... ok
...
----------------------------------------------------------------------
Ran 31 tests in 0.234s

OK
```

### Failure Output
```
FAIL: test_something (tests.test_phase1.TestClass)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tests/test_phase1.py", line XX, in test_something
    self.assertTrue(condition)
AssertionError: False is not true

----------------------------------------------------------------------
Ran 31 tests in 0.245s

FAILED (failures=1)
```

---

## Troubleshooting

### Issue: "No module named 'app'"
**Solution:** Run tests from repository root directory:
```bash
cd /path/to/Jangira-AutoPrint
python -m unittest tests.test_phase1 -v
```

### Issue: "No printers found" in PrinterManager tests
**Solution:** This is normal on systems without printers configured. Tests handle this gracefully.

### Issue: Database tests fail with permission errors
**Solution:** Ensure write permissions in temporary directory:
```bash
chmod 755 /tmp
```

### Issue: Some tests timeout
**Solution:** Reduce system load or increase timeout values in config.py:
```python
PRINT_TIMEOUT = 120  # Increase from 60
QUEUE_POLL_INTERVAL = 5  # Increase from 2
```

---

## Test Execution Plan

### Phase 1A: Unit Tests (Individual Components)
1. Logger Tests (2 tests)
2. Database Tests (6 tests)
3. Configuration Tests (3 tests)

**Time:** ~5 seconds
**Expected:** 11/11 PASS ✅

### Phase 1B: Dependency Tests (External Systems)
1. Printer Manager Tests (3 tests)
2. PDF Validator Tests (3 tests)

**Time:** ~3 seconds
**Expected:** 6/6 PASS ✅

### Phase 1C: Core Functionality Tests
1. PDF Manager Tests (3 tests)
2. PDF Processor Tests (2 tests)
3. Job Executor Tests (4 tests)
4. Job Queue Tests (3 tests)

**Time:** ~8 seconds
**Expected:** 12/12 PASS ✅

### Phase 1D: Integration Tests
1. Integration Tests (2 tests)

**Time:** ~2 seconds
**Expected:** 2/2 PASS ✅

**Total Execution Time:** ~18 seconds
**Total Expected:** 31/31 PASS ✅

---

## Continuous Integration

### GitHub Actions Example
```yaml
name: Phase 1 Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - run: pip install -r requirements.txt
      - run: python -m unittest tests.test_phase1 -v
```

---

## Coverage Report

To generate a coverage report (requires `coverage` package):

```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run -m unittest tests.test_phase1

# Generate report
coverage report -m

# Generate HTML report
coverage html
open htmlcov/index.html
```

---

## Next Steps After Testing

If all 31 tests pass ✅:
1. Review test results
2. Check database integrity
3. Verify printer detection works
4. Test UI manually (run `python run.py`)
5. Test real print job submission
6. Document any system-specific configurations
7. Proceed to Phase 2

If tests fail ❌:
1. Check error messages
2. Review related module code
3. Check system dependencies
4. Verify configuration values
5. Run individual test for debugging
6. Report issues

---

## Test Maintenance

After making code changes:

```bash
# Run tests to verify changes don't break functionality
python -m unittest tests.test_phase1 -v

# If tests fail, identify the issue
# Make necessary fixes
# Re-run tests until all pass

# Update tests if new functionality added
```

---

**Last Updated:** September 1, 2026
**Status:** Ready for Testing
**Total Test Cases:** 31
**Expected Pass Rate:** 100%
