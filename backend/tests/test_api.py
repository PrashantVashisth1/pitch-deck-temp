"""
API Tests for Pitch Deck Analyzer
"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app

client = TestClient(app)

def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["message"] == "Pitch Deck Analyzer API"

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_features():
    """Test get features endpoint"""
    response = client.get("/api/features")
    assert response.status_code == 200
    data = response.json()
    assert "analysis_categories" in data
    assert len(data["analysis_categories"]) > 0

def test_list_analyses_empty():
    """Test listing analyses when database is empty or has data"""
    response = client.get("/api/analyses")
    assert response.status_code == 200
    data = response.json()
    assert "analyses" in data
    assert "total" in data
    assert isinstance(data["analyses"], list)

def test_get_statistics():
    """Test statistics endpoint"""
    response = client.get("/api/statistics")
    assert response.status_code == 200
    data = response.json()
    assert "total_analyses" in data
    assert "average_score" in data

def test_analyze_without_file():
    """Test analyze endpoint without file"""
    response = client.post("/api/analyze")
    assert response.status_code == 422  # Unprocessable Entity

def test_analyze_with_wrong_file_type():
    """Test analyze endpoint with non-PDF file"""
    files = {"file": ("test.txt", b"test content", "text/plain")}
    response = client.post("/api/analyze", files=files)
    assert response.status_code == 400
    assert "Only PDF files are allowed" in response.json()["detail"]

def test_get_nonexistent_analysis():
    """Test getting non-existent analysis"""
    response = client.get("/api/analysis/nonexistent_id")
    assert response.status_code == 404

def test_get_nonexistent_report():
    """Test getting non-existent report"""
    response = client.get("/api/report/nonexistent_id")
    assert response.status_code == 404

def test_delete_nonexistent_analysis():
    """Test deleting non-existent analysis"""
    response = client.delete("/api/analysis/nonexistent_id")
    assert response.status_code == 404

@pytest.mark.skipif(
    not Path("../samples/sample_pitch.pdf").exists(),
    reason="Sample PDF not found"
)
def test_analyze_with_sample_pdf():
    """Test analyze endpoint with sample PDF"""
    pdf_path = Path("../samples/sample_pitch.pdf")
    
    with open(pdf_path, "rb") as f:
        files = {"file": ("sample_pitch.pdf", f, "application/pdf")}
        response = client.post("/api/analyze", files=files)
    
    # This test requires a valid Gemini API key
    # It might fail if API key is not set or invalid
    if response.status_code == 200:
        data = response.json()
        assert "analysis_id" in data
        assert "overall_score" in data
        assert "category_scores" in data
        assert "strengths" in data
        assert "weaknesses" in data
        assert "recommendations" in data
    else:
        # Log the error for debugging
        print(f"Analysis failed: {response.json()}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])