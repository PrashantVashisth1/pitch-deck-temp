"""
AI Analysis Engine using Google Gemini for pitch deck evaluation
"""
import google.generativeai as genai
import json
import logging
from typing import Dict, List
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class AIAnalyzer:
    """Analyzes pitch decks using Gemini AI"""
    
    def __init__(self, api_key: str = None, features_file: str = None):
        """
        Initialize the AI Analyzer
        
        Args:
            api_key: Gemini API key
            features_file: Path to Evalyze features JSON
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        genai.configure(api_key=self.api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Load analysis features
        self.features = self._load_features(features_file)
        self.categories = self.features.get("analysis_categories", [])
    
    def _load_features(self, features_file: str = None) -> Dict:
        """Load Evalyze features for analysis"""
        if features_file and Path(features_file).exists():
            with open(features_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Return default features if file not found
        return {
            "analysis_categories": [
                {"name": "Problem & Solution", "weight": 20},
                {"name": "Market Opportunity", "weight": 15},
                {"name": "Business Model", "weight": 15},
                {"name": "Competitive Advantage", "weight": 15},
                {"name": "Traction & Validation", "weight": 15},
                {"name": "Team", "weight": 10},
                {"name": "Financial Projections", "weight": 10}
            ]
        }
    
    def analyze_pitch_deck(self, extracted_data: Dict) -> Dict:
        """
        Analyze a pitch deck and generate comprehensive evaluation
        
        Args:
            extracted_data: Dictionary from PDFProcessor
            
        Returns:
            Complete analysis results
        """
        logger.info(f"Analyzing pitch deck: {extracted_data.get('filename', 'unknown')}")
        
        text_content = extracted_data.get("text_content", "")
        metadata = extracted_data.get("metadata", {})
        structure = extracted_data.get("structure", {})
        
        # Analyze each category
        category_scores = {}
        category_feedback = {}
        
        for category in self.categories:
            cat_name = category["name"]
            logger.info(f"Analyzing category: {cat_name}")
            
            score, feedback = self._analyze_category(
                cat_name, 
                text_content, 
                structure
            )
            
            category_scores[cat_name] = score
            category_feedback[cat_name] = feedback
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(category_scores)
        
        # Generate strengths and weaknesses
        strengths = self._extract_strengths(category_feedback, category_scores)
        weaknesses = self._extract_weaknesses(category_feedback, category_scores)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            category_scores, 
            category_feedback
        )
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            overall_score,
            strengths,
            weaknesses
        )
        
        return {
            "overall_score": overall_score,
            "category_scores": category_scores,
            "category_feedback": category_feedback,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "executive_summary": executive_summary,
            "extracted_text": text_content[:5000],  # Store sample for training
            "metadata": metadata
        }
    
    def _analyze_category(self, category_name: str, content: str, structure: Dict) -> tuple:
        """Analyze a specific category"""
        
        # Create focused prompt for category
        prompt = f"""
You are an expert venture capital analyst evaluating a pitch deck.

Analyze the following pitch deck content specifically for: **{category_name}**

Pitch Deck Content:
{content[:4000]}  # Limit content to stay within token limits

Structure Info:
- Page Count: {structure.get('page_count', 'Unknown')}
- Has Images: {structure.get('has_images', False)}
- Sections: {', '.join([s.get('title', '') for s in structure.get('estimated_sections', [])])}

Evaluation Criteria for {category_name}:
- Clarity and completeness of information
- Evidence and data quality
- Persuasiveness and credibility
- Professional presentation

Provide your analysis in this EXACT JSON format (no additional text):
{{
    "score": <number 0-100>,
    "analysis": "<detailed analysis in 2-3 sentences>",
    "key_points": ["<point 1>", "<point 2>", "<point 3>"]
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Extract JSON from response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(result_text)
            
            score = min(100, max(0, float(result.get("score", 50))))
            feedback = {
                "analysis": result.get("analysis", "No analysis available"),
                "key_points": result.get("key_points", [])
            }
            
            return score, feedback
            
        except Exception as e:
            logger.error(f"Error analyzing {category_name}: {str(e)}")
            # Return default score and feedback
            return 50.0, {
                "analysis": f"Unable to analyze {category_name} due to processing error",
                "key_points": []
            }
    
    def _calculate_overall_score(self, category_scores: Dict) -> float:
        """Calculate weighted overall score"""
        total_score = 0
        total_weight = 0
        
        for category in self.categories:
            cat_name = category["name"]
            weight = category.get("weight", 10)
            score = category_scores.get(cat_name, 0)
            
            total_score += score * weight
            total_weight += weight
        
        return round(total_score / total_weight if total_weight > 0 else 0, 2)
    
    def _extract_strengths(self, feedback: Dict, scores: Dict) -> List[str]:
        """Extract key strengths from high-scoring categories"""
        strengths = []
        
        # Get categories with scores above 70
        strong_categories = [
            cat for cat, score in scores.items() if score >= 70
        ]
        
        for cat in strong_categories[:3]:  # Top 3 strengths
            cat_feedback = feedback.get(cat, {})
            analysis = cat_feedback.get("analysis", "")
            if analysis:
                strengths.append(f"**{cat}**: {analysis}")
        
        return strengths if strengths else ["Pitch deck shows potential in foundational areas"]
    
    def _extract_weaknesses(self, feedback: Dict, scores: Dict) -> List[str]:
        """Extract key weaknesses from low-scoring categories"""
        weaknesses = []
        
        # Get categories with scores below 60
        weak_categories = [
            (cat, score) for cat, score in scores.items() if score < 60
        ]
        weak_categories.sort(key=lambda x: x[1])  # Sort by score ascending
        
        for cat, score in weak_categories[:3]:  # Top 3 weaknesses
            cat_feedback = feedback.get(cat, {})
            analysis = cat_feedback.get("analysis", "")
            if analysis:
                weaknesses.append(f"**{cat}** (Score: {score:.0f}): {analysis}")
        
        return weaknesses if weaknesses else ["No major weaknesses identified"]
    
    def _generate_recommendations(self, scores: Dict, feedback: Dict) -> List[str]:
        """Generate actionable recommendations"""
        
        # Find lowest scoring categories
        sorted_cats = sorted(scores.items(), key=lambda x: x[1])
        
        recommendations = []
        
        prompt = f"""
Based on this pitch deck analysis, provide 5 specific, actionable recommendations for improvement.

Category Scores:
{json.dumps(scores, indent=2)}

Focus on the lowest scoring areas. Each recommendation should be:
- Specific and actionable
- Focused on one clear improvement
- Professional and constructive

Return ONLY a JSON array of strings, no additional text:
["recommendation 1", "recommendation 2", "recommendation 3", "recommendation 4", "recommendation 5"]
"""
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Extract JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            recommendations = json.loads(result_text)
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            # Fallback recommendations
            for cat, score in sorted_cats[:3]:
                recommendations.append(
                    f"Strengthen the {cat} section with more detailed information and supporting data"
                )
        
        return recommendations[:5]
    
    def _generate_executive_summary(self, overall_score: float, 
                                    strengths: List[str], 
                                    weaknesses: List[str]) -> str:
        """Generate executive summary"""
        
        prompt = f"""
Write a concise executive summary (3-4 sentences) for a pitch deck that scored {overall_score:.1f}/100.

Key Strengths:
{chr(10).join(f"- {s}" for s in strengths[:3])}

Key Weaknesses:
{chr(10).join(f"- {w}" for w in weaknesses[:3])}

The summary should be professional, balanced, and provide a clear overall assessment.
Return ONLY the summary text, no additional formatting.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating executive summary: {str(e)}")
            
            # Fallback summary
            quality = "strong" if overall_score >= 70 else "moderate" if overall_score >= 50 else "developing"
            return f"This pitch deck demonstrates {quality} potential with an overall score of {overall_score:.1f}/100. While there are notable strengths in key areas, there are opportunities for improvement that could significantly enhance the pitch's effectiveness."