"""
Tests for PDF Processor Module
"""
import pytest
from pathlib import Path
import sys
import io

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pdf_processor import PDFProcessor

@pytest.fixture
def pdf_processor():
    """Create a PDF processor instance"""
    return PDFProcessor()

@pytest.fixture
def sample_pdf_path():
    """Path to sample PDF (if exists)"""
    return Path("../samples/sample_pitch.pdf")

def test_processor_initialization(pdf_processor):
    """Test that processor initializes correctly"""
    assert pdf_processor is not None
    assert isinstance(pdf_processor, PDFProcessor)

def test_process_nonexistent_pdf(pdf_processor):
    """Test processing a non-existent PDF raises error"""
    with pytest.raises(FileNotFoundError):
        pdf_processor.process_pdf("nonexistent.pdf")

@pytest.mark.skipif(
    not Path("../samples/sample_pitch.pdf").exists(),
    reason="Sample PDF not found"
)
def test_process_existing_pdf(pdf_processor, sample_pdf_path):
    """Test processing an existing PDF"""
    result = pdf_processor.process_pdf(str(sample_pdf_path))
    
    # Check structure
    assert "filename" in result
    assert "text_content" in result
    assert "page_count" in result
    assert "word_count" in result
    assert "metadata" in result
    assert "structure" in result
    
    # Check values
    assert result["filename"] == "sample_pitch.pdf"
    assert result["page_count"] > 0
    assert result["word_count"] >= 0
    assert isinstance(result["text_content"], str)
    assert isinstance(result["metadata"], dict)

def test_process_pdf_bytes(pdf_processor, sample_pdf_path):
    """Test processing PDF from bytes"""
    if not sample_pdf_path.exists():
        pytest.skip("Sample PDF not found")
    
    # Read PDF as bytes
    with open(sample_pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    result = pdf_processor.process_pdf_bytes(pdf_bytes, "test.pdf")
    
    assert result["filename"] == "test.pdf"
    assert "text_content" in result
    assert "page_count" in result

def test_extracted_structure(pdf_processor, sample_pdf_path):
    """Test that structure is properly extracted"""
    if not sample_pdf_path.exists():
        pytest.skip("Sample PDF not found")
    
    result = pdf_processor.process_pdf(str(sample_pdf_path))
    
    structure = result["structure"]
    assert "page_count" in structure
    assert "has_images" in structure
    assert "estimated_sections" in structure
    assert isinstance(structure["estimated_sections"], list)

def test_looks_like_header(pdf_processor):
    """Test header detection heuristic"""
    # Test various header patterns
    assert pdf_processor._looks_like_header("PROBLEM") == True
    assert pdf_processor._looks_like_header("Market Opportunity") == True
    assert pdf_processor._looks_like_header("Our Solution:") == True
    assert pdf_processor._looks_like_header("TEAM") == True
    
    # These should not be headers
    assert pdf_processor._looks_like_header("This is a long sentence that is not a header") == False
    assert pdf_processor._looks_like_header("a") == False

def test_word_count_calculation(pdf_processor, sample_pdf_path):
    """Test that word count is calculated correctly"""
    if not sample_pdf_path.exists():
        pytest.skip("Sample PDF not found")
    
    result = pdf_processor.process_pdf(str(sample_pdf_path))
    
    # Count words manually from text
    text = result["text_content"]
    manual_count = len(text.split())
    
    assert result["word_count"] == manual_count

def test_metadata_extraction(pdf_processor, sample_pdf_path):
    """Test that PDF metadata is extracted"""
    if not sample_pdf_path.exists():
        pytest.skip("Sample PDF not found")
    
    result = pdf_processor.process_pdf(str(sample_pdf_path))
    
    metadata = result["metadata"]
    assert isinstance(metadata, dict)
    
    # Metadata keys (may be empty but should exist)
    expected_keys = ["title", "author", "subject", "creator"]
    for key in expected_keys:
        assert key in metadata

def test_empty_pdf_handling(pdf_processor, tmp_path):
    """Test handling of empty or corrupt PDF"""
    # Create a fake empty file
    empty_pdf = tmp_path / "empty.pdf"
    empty_pdf.write_bytes(b"")
    
    with pytest.raises(Exception):
        pdf_processor.process_pdf(str(empty_pdf))

def test_image_detection(pdf_processor, sample_pdf_path):
    """Test that images are detected in PDF"""
    if not sample_pdf_path.exists():
        pytest.skip("Sample PDF not found")
    
    result = pdf_processor.process_pdf(str(sample_pdf_path))
    
    # has_images should be a boolean
    assert isinstance(result["has_images"], bool)
    assert isinstance(result["structure"]["has_images"], bool)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])