"""PDF Processing and Management"""

import hashlib
import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional, List, Tuple
from app.config import MAX_FILE_SIZE, MAX_PAGES, TEMP_DIR, TEMP_RENDER_PREFIX
from app.logger import JangiraLogger

class PDFValidator:
    """Validates PDF files"""
    
    def __init__(self):
        self.logger = JangiraLogger.get_logger()
    
    def validate_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate PDF file"""
        try:
            path = Path(file_path)
            
            # Check file exists
            if not path.exists():
                return False, "File does not exist"
            
            # Check file size
            if path.stat().st_size > MAX_FILE_SIZE:
                return False, f"File size exceeds {MAX_FILE_SIZE / 1024 / 1024:.0f}MB limit"
            
            # Check file extension
            if path.suffix.lower() != '.pdf':
                return False, "File is not a PDF"
            
            # Try to open PDF
            try:
                doc = fitz.open(file_path)
                page_count = doc.page_count
                doc.close()
                
                if page_count == 0:
                    return False, "PDF has no pages"
                
                if page_count > MAX_PAGES:
                    return False, f"PDF exceeds {MAX_PAGES} page limit"
                
                return True, None
            except Exception as e:
                return False, f"Invalid PDF: {str(e)}"
        except Exception as e:
            self.logger.error(f"Error validating PDF: {e}")
            return False, str(e)
    
    def calculate_sha256(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

class PDFManager:
    """Manages PDF operations"""
    
    def __init__(self):
        self.logger = JangiraLogger.get_logger()
        self.validator = PDFValidator()
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    def get_page_count(self, file_path: str) -> int:
        """Get number of pages in PDF"""
        try:
            doc = fitz.open(file_path)
            count = doc.page_count
            doc.close()
            return count
        except Exception as e:
            self.logger.error(f"Error getting page count: {e}")
            return 0
    
    def get_pdf_info(self, file_path: str) -> dict:
        """Get PDF information"""
        try:
            doc = fitz.open(file_path)
            info = {
                "page_count": doc.page_count,
                "is_pdf": True,
                "is_encrypted": doc.is_pdf and doc.is_encrypted,
                "metadata": doc.metadata
            }
            doc.close()
            return info
        except Exception as e:
            self.logger.error(f"Error getting PDF info: {e}")
            return {"error": str(e)}
    
    def validate_page_range(self, file_path: str, page_spec: str) -> Tuple[bool, Optional[str]]:
        """Validate page specification"""
        try:
            page_count = self.get_page_count(file_path)
            
            if not page_spec or page_spec.strip() == "":
                return True, None
            
            # Parse page specification (e.g., "1,3,5-10")
            pages_to_check = set()
            parts = page_spec.split(',')
            
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # Range like "5-10"
                    try:
                        start, end = map(int, part.split('-'))
                        if start < 1 or end > page_count or start > end:
                            return False, f"Invalid page range: {part}"
                        pages_to_check.update(range(start, end + 1))
                    except ValueError:
                        return False, f"Invalid page range format: {part}"
                else:
                    # Single page
                    try:
                        page = int(part)
                        if page < 1 or page > page_count:
                            return False, f"Page {page} out of range (1-{page_count})"
                        pages_to_check.add(page)
                    except ValueError:
                        return False, f"Invalid page number: {part}"
            
            return True, None
        except Exception as e:
            self.logger.error(f"Error validating page range: {e}")
            return False, str(e)
    
    def extract_pages(self, file_path: str, page_spec: str) -> Optional[Path]:
        """Extract specific pages from PDF"""
        try:
            doc = fitz.open(file_path)
            new_doc = fitz.open()
            
            # Parse page specification
            pages = []
            if page_spec and page_spec.strip():
                parts = page_spec.split(',')
                for part in parts:
                    part = part.strip()
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        pages.extend(range(start - 1, end))  # Convert to 0-indexed
                    else:
                        pages.append(int(part) - 1)  # Convert to 0-indexed
            else:
                # All pages
                pages = range(doc.page_count)
            
            # Copy selected pages
            for page_num in pages:
                if 0 <= page_num < doc.page_count:
                    new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            
            doc.close()
            
            # Save extracted PDF
            output_path = TEMP_DIR / f"{TEMP_RENDER_PREFIX}{hashlib.md5(str(file_path).encode()).hexdigest()}.pdf"
            new_doc.save(output_path)
            new_doc.close()
            
            self.logger.info(f"Extracted {len(pages)} pages to {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"Error extracting pages: {e}")
            return None
    
    def get_printable_path(self, file_path: str, page_spec: str) -> Tuple[str, bool]:
        """Get the actual file path to print"""
        if page_spec and page_spec.strip():
            # Extract specific pages
            extracted_path = self.extract_pages(file_path, page_spec)
            if extracted_path:
                return str(extracted_path), True
        
        return file_path, False
    
    def cleanup_temp_files(self):
        """Clean up temporary extracted PDFs"""
        try:
            for temp_file in TEMP_DIR.glob(f"{TEMP_RENDER_PREFIX}*.pdf"):
                try:
                    temp_file.unlink()
                    self.logger.debug(f"Cleaned up temp file: {temp_file}")
                except Exception as e:
                    self.logger.warning(f"Could not delete temp file {temp_file}: {e}")
        except Exception as e:
            self.logger.error(f"Error cleaning up temp files: {e}")

class PDFProcessor:
    """High-level PDF processing"""
    
    def __init__(self):
        self.logger = JangiraLogger.get_logger()
        self.validator = PDFValidator()
        self.manager = PDFManager()
    
    def process_pdf(self, file_path: str, page_spec: str = "") -> Tuple[bool, Optional[str], dict]:
        """Process and validate PDF"""
        try:
            # Validate file
            is_valid, error = self.validator.validate_file(file_path)
            if not is_valid:
                return False, error, {}
            
            # Get page count
            page_count = self.manager.get_page_count(file_path)
            
            # Validate page specification
            if page_spec:
                is_valid, error = self.manager.validate_page_range(file_path, page_spec)
                if not is_valid:
                    return False, error, {}
            
            # Calculate hash
            file_hash = self.validator.calculate_sha256(file_path)
            
            info = {
                "file_path": file_path,
                "page_count": page_count,
                "page_spec": page_spec,
                "sha256": file_hash
            }
            
            return True, None, info
        except Exception as e:
            self.logger.error(f"Error processing PDF: {e}")
            return False, str(e), {}
