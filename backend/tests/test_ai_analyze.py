"""
Tests for AI Analyzer Module
"""
import pytest
from pathlib import Path
import sys
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_analyzer import AIAnalyzer

# Skip all tests if API key is not available
pytestmark = pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY not set"
)

@pytest.fixture
def analyzer():
    """Create an AI analyzer instance"""
    api_key = os.getenv("GEMINI_API_KEY")
    return AIAnalyzer(api_key=api_key)

@pytest.fixture
def sample_extracted_data():
    """Sample extracted data from PDF processor"""
    return {
        "filename": "test_pitch.pdf",
        "text_content": """
        Problem: Small businesses struggle with managing inventory efficiently.
        Solution: Our AI-powered inventory management system automates tracking and ordering.
        Market: The global inventory management market is worth $2.1B and growing at 8% annually.
        Business Model: SaaS subscription starting at $99/month with enterprise plans up to $999/month.
        Team: Our founding team has 20+ years of combined experience in supply chain and AI.
        Traction: 50 beta customers, $50K MRR, 95% customer satisfaction.
        Financial Projections: Targeting $1M ARR in year 1, $5M in year 2.
        """,
        "page_count": 12,
        "word_count": 150,
        "metadata": {
            "title": "Test Pitch Deck",
            "author": "Test Startup"
        },
        "structure": {
            "page_count": 12,
            "has_images": True,
            "estimated_sections": [
                {"title": "Problem", "page": 2},
                {"title": "Solution", "page": 3},
                {"title": "Market", "page": 5},
                {"title": "Team", "page": 9}
            ]
        }
    }

def test_analyzer_initialization(analyzer):
    """Test that analyzer initializes correctly"""
    assert analyzer is not None
    assert isinstance(analyzer, AIAnalyzer)
    assert analyzer.model is not None
    assert len(analyzer.categories) > 0

def test_analyzer_without_api_key():
    """Test that analyzer raises error without API key"""
    with pytest.raises(ValueError):
        AIAnalyzer(api_key=None)

def test_load_default_features(analyzer):
    """Test loading default features"""
    assert "analysis_categories" in analyzer.features
    categories = analyzer.features["analysis_categories"]
    assert len(categories) > 0
    assert all("name" in cat for cat in categories)
    assert all("weight" in cat for cat in categories)

def test_analyze_pitch_deck_structure(analyzer, sample_extracted_data):
    """Test that analysis returns correct structure"""
    result = analyzer.analyze_pitch_deck(sample_extracted_data)
    
    # Check all required keys
    required_keys = [
        "overall_score",
        "category_scores",
        "category_feedback",
        "strengths",
        "weaknesses",
        "recommendations",
        "executive_summary"
    ]
    
    for key in required_keys:
        assert key in result, f"Missing key: {key}"

def test_overall_score_range(analyzer, sample_extracted_data):
    """Test that overall score is within valid range"""
    result = analyzer.analyze_pitch_deck(sample_extracted_data)
    
    overall_score = result["overall_score"]
    assert isinstance(overall_score, (int, float))
    assert 0 <= overall_score <= 100

def test_category_scores(analyzer, sample_extracted_data):
    """Test that all categories are scored"""
    result = analyzer.analyze_pitch_deck(sample_extracted_data)
    
    category_scores = result["category_scores"]
    assert isinstance(category_scores, dict)
    assert len(category_scores) > 0
    
    # Check each score is valid
    for category, score in category_scores.items():
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100

def test_category_feedback_structure(analyzer, sample_extracted_data):
    """Test that category feedback has correct structure"""
    result = analyzer.analyze_pitch_deck(sample_extracted_data)
    
    category_feedback = result["category_feedback"]
    assert isinstance(category_feedback, dict)
    
    # Each feedback should have analysis and key_points
    for category, feedback in category_feedback.items():
        assert "analysis" in feedback
        assert "key_points" in feedback
        assert isinstance(feedback["analysis"], str)
        assert isinstance(feedback["key_points"], list)

def test_strengths_list(analyzer, sample_extracted_data):
    """Test that strengths are properly extracted"""
    result = analyzer.analyze_pitch_deck(sample_extracted_data)
    
    strengths = result["strengths"]
    assert isinstance(strengths, list)
    assert len(strengths) > 0
    assert all(isinstance(s, str) for s in strengths)

def test_weaknesses_list(analyzer, sample_extracted_data):
    """Test that weaknesses are properly identified"""
    result = analyzer.analyze_pitch_deck(sample_extracted_data)
    
    weaknesses = result["weaknesses"]
    assert isinstance(weaknesses, list)
    assert len(weaknesses) > 0
    assert all(isinstance(w, str) for w in weaknesses)

def test_recommendations_list(analyzer, sample_extracted_data):
    """Test that recommendations are generated"""
    result = analyzer.analyze_pitch_deck(sample_extracted_data)
    
    recommendations = result["recommendations"]
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0
    assert len(recommendations) <= 5  # Should return max 5
    assert all(isinstance(r, str) for r in recommendations)

def test_executive_summary(analyzer, sample_extracted_data):
    """Test that executive summary is generated"""
    result = analyzer.analyze_pitch_deck(sample_extracted_data)
    
    summary = result["executive_summary"]
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert len(summary) < 1000  # Should be concise

def test_calculate_overall_score(analyzer):
    """Test overall score calculation"""
    category_scores = {
        "Problem & Solution": 80,
        "Market Opportunity": 70,
        "Business Model": 60,
        "Competitive Advantage": 75,
        "Traction & Validation": 65,
        "Team": 70,
        "Financial Projections": 60
    }
    
    overall = analyzer._calculate_overall_score(category_scores)
    assert isinstance(overall, float)
    assert 0 <= overall <= 100

def test_extract_strengths(analyzer):
    """Test strength extraction logic"""
    feedback = {
        "Category A": {"analysis": "Strong performance", "key_points": []},
        "Category B": {"analysis": "Good execution", "key_points": []},
        "Category C": {"analysis": "Needs improvement", "key_points": []}
    }
    scores = {
        "Category A": 85,
        "Category B": 75,
        "Category C": 45
    }
    
    strengths = analyzer._extract_strengths(feedback, scores)
    assert isinstance(strengths, list)
    assert len(strengths) > 0

def test_extract_weaknesses(analyzer):
    """Test weakness extraction logic"""
    feedback = {
        "Category A": {"analysis": "Strong performance", "key_points": []},
        "Category B": {"analysis": "Good execution", "key_points": []},
        "Category C": {"analysis": "Needs improvement", "key_points": []}
    }
    scores = {
        "Category A": 85,
        "Category B": 75,
        "Category C": 45
    }
    
    weaknesses = analyzer._extract_weaknesses(feedback, scores)
    assert isinstance(weaknesses, list)
    assert len(weaknesses) > 0

def test_analyze_with_minimal_content(analyzer):
    """Test analysis with minimal content"""
    minimal_data = {
        "filename": "minimal.pdf",
        "text_content": "Problem: Issue. Solution: Fix.",
        "page_count": 1,
        "word_count": 5,
        "metadata": {},
        "structure": {
            "page_count": 1,
            "has_images": False,
            "estimated_sections": []
        }
    }
    
    result = analyzer.analyze_pitch_deck(minimal_data)
    
    # Should still return valid structure even with minimal content
    assert "overall_score" in result
    assert "category_scores" in result
    assert isinstance(result["overall_score"], (int, float))

def test_analyze_with_empty_content(analyzer):
    """Test analysis with empty content"""
    empty_data = {
        "filename": "empty.pdf",
        "text_content": "",
        "page_count": 0,
        "word_count": 0,
        "metadata": {},
        "structure": {
            "page_count": 0,
            "has_images": False,
            "estimated_sections": []
        }
    }
    
    result = analyzer.analyze_pitch_deck(empty_data)
    
    # Should handle gracefully
    assert "overall_score" in result
    assert result["overall_score"] >= 0

def test_category_weights_sum(analyzer):
    """Test that category weights are properly configured"""
    total_weight = sum(cat["weight"] for cat in analyzer.categories)
    assert total_weight == 100  # Weights should sum to 100

if __name__ == "__main__":
    pytest.main([__file__, "-v"])