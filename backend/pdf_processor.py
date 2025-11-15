"""
PDF Processing Module for extracting content from pitch deck PDFs
"""
import PyPDF2
import pdfplumber
from PIL import Image
import io
import logging
from typing import Dict, List
from pathlib import Path
import re

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Processes PDF files and extracts content"""
    
    def __init__(self):
        """Initialize PDF processor"""
        pass
    
    def process_pdf(self, pdf_path: str) -> Dict:
        """
        Process a PDF file and extract all content
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with extracted data
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Processing PDF: {pdf_path.name}")
        
        with open(pdf_path, 'rb') as file:
            return self._extract_content(file, pdf_path.name)
    
    def process_pdf_bytes(self, pdf_bytes: bytes, filename: str) -> Dict:
        """
        Process PDF from bytes
        
        Args:
            pdf_bytes: PDF file content as bytes
            filename: Original filename
            
        Returns:
            Dictionary with extracted data
        """
        logger.info(f"Processing PDF bytes: {filename}")
        
        pdf_file = io.BytesIO(pdf_bytes)
        return self._extract_content(pdf_file, filename)
    
    def _extract_content(self, pdf_file, filename: str) -> Dict:
        """Extract all content from PDF"""
        
        # Initialize result structure
        result = {
            "filename": filename,
            "text_content": "",
            "page_count": 0,
            "word_count": 0,
            "has_images": False,
            "metadata": {},
            "structure": {
                "page_count": 0,
                "has_images": False,
                "estimated_sections": []
            }
        }
        
        try:
            # Extract text using PyPDF2
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            result["page_count"] = len(pdf_reader.pages)
            result["structure"]["page_count"] = len(pdf_reader.pages)
            
            # Extract metadata
            if pdf_reader.metadata:
                result["metadata"] = {
                    "title": pdf_reader.metadata.get('/Title', ''),
                    "author": pdf_reader.metadata.get('/Author', ''),
                    "subject": pdf_reader.metadata.get('/Subject', ''),
                    "creator": pdf_reader.metadata.get('/Creator', ''),
                }
            
            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {str(e)}")
            
            result["text_content"] = "\n".join(text_parts)
            
            # Reset file pointer for pdfplumber
            pdf_file.seek(0)
            
            # Use pdfplumber for better text extraction and structure
            with pdfplumber.open(pdf_file) as pdf:
                enhanced_text = []
                sections = []
                
                for page_num, page in enumerate(pdf.pages):
                    # Extract text with layout
                    page_text = page.extract_text()
                    if page_text:
                        enhanced_text.append(page_text)
                        
                        # Try to identify section headers (larger font, bold, etc.)
                        lines = page_text.split('\n')
                        for line in lines:
                            # Simple heuristic: short lines (< 50 chars) might be headers
                            if len(line.strip()) > 0 and len(line.strip()) < 50:
                                if self._looks_like_header(line):
                                    sections.append({
                                        "title": line.strip(),
                                        "page": page_num + 1
                                    })
                    
                    # Check for images
                    if page.images:
                        result["has_images"] = True
                        result["structure"]["has_images"] = True
                
                # Use enhanced text if better
                if len("\n".join(enhanced_text)) > len(result["text_content"]):
                    result["text_content"] = "\n".join(enhanced_text)
                
                result["structure"]["estimated_sections"] = sections
            
            # Calculate word count
            result["word_count"] = len(result["text_content"].split())
            
            logger.info(f"Successfully processed {filename}: {result['page_count']} pages, {result['word_count']} words")
            
        except Exception as e:
            logger.error(f"Error processing PDF {filename}: {str(e)}")
            raise
        
        return result
    
    def _looks_like_header(self, text: str) -> bool:
        """Simple heuristic to identify potential section headers"""
        text = text.strip()
        
        # Common header patterns
        header_keywords = [
            'problem', 'solution', 'market', 'product', 'business model',
            'team', 'traction', 'competition', 'financial', 'projections',
            'vision', 'mission', 'overview', 'introduction', 'summary',
            'opportunity', 'strategy', 'revenue', 'growth', 'roadmap'
        ]
        
        text_lower = text.lower()
        
        # Check if it's all caps (common for headers)
        if text.isupper() and len(text) > 3:
            return True
        
        # Check if it contains header keywords
        for keyword in header_keywords:
            if keyword in text_lower:
                return True
        
        # Check if it ends with colon (common for headers)
        if text.endswith(':'):
            return True
        
        return False
    
    def extract_images(self, pdf_path: str, output_dir: str = None) -> List[str]:
        """
        Extract images from PDF
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save images (optional)
            
        Returns:
            List of image paths
        """
        pdf_path = Path(pdf_path)
        
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = pdf_path.parent / f"{pdf_path.stem}_images"
            output_dir.mkdir(parents=True, exist_ok=True)
        
        image_paths = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    for img_num, img in enumerate(page.images):
                        try:
                            # Extract image
                            img_path = output_dir / f"page{page_num + 1}_img{img_num + 1}.png"
                            
                            # This is a simplified version - actual implementation
                            # would need more complex image extraction
                            image_paths.append(str(img_path))
                            
                        except Exception as e:
                            logger.warning(f"Error extracting image from page {page_num}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting images from {pdf_path}: {str(e)}")
        
        return image_paths