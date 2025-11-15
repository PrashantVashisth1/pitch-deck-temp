"""
Web Scraper for Evalyze.ai to extract pitch deck analysis features
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import time

logger = logging.getLogger(__name__)

class EvalyzeScraper:
    """Scrapes Evalyze.ai to extract analysis features and criteria"""
    
    def __init__(self, data_dir: str = "../data"):
        """
        Initialize scraper
        
        Args:
            data_dir: Directory to save scraped data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.features_file = self.data_dir / "evalyze_features.json"
    
    def scrape_features(self, url: str = None) -> Dict:
        """
        Scrape Evalyze.ai to extract pitch deck analysis features
        
        Args:
            url: URL to scrape (optional)
            
        Returns:
            Dictionary with scraped features
        """
        if not url:
            url = "https://www.evalyze.ai/startups/cmgypekfy0008vy9p3l2p2rag/pitchdecks"
        
        logger.info(f"Scraping features from: {url}")
        
        try:
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Initialize driver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            try:
                # Load page
                driver.get(url)
                
                # Wait for content to load
                wait = WebDriverWait(driver, 10)
                time.sleep(3)  # Additional wait for dynamic content
                
                # Get page source
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Extract features
                features = self._extract_features_from_page(soup)
                
                # Save features
                self._save_features(features)
                
                logger.info("Successfully scraped features from Evalyze.ai")
                return features
                
            finally:
                driver.quit()
        
        except Exception as e:
            logger.error(f"Error scraping Evalyze: {str(e)}")
            logger.info("Using default features as fallback")
            return self._get_default_features()
    
    def _extract_features_from_page(self, soup: BeautifulSoup) -> Dict:
        """Extract analysis features from page HTML"""
        
        features = {
            "scraped_at": datetime.now().isoformat(),
            "source": "evalyze.ai",
            "analysis_categories": [],
            "evaluation_criteria": []
        }
        
        try:
            # Try to find score/category elements
            # This is a generic approach - adjust selectors based on actual page structure
            
            # Look for category names and scores
            category_elements = soup.find_all(['h2', 'h3', 'h4', 'div', 'span'], 
                                             class_=lambda x: x and ('category' in x.lower() or 
                                                                    'score' in x.lower() or
                                                                    'section' in x.lower() or
                                                                    'metric' in x.lower()))
            
            # Common pitch deck categories
            detected_categories = set()
            
            # Also search in all text content
            all_text = soup.get_text().lower()
            
            # Keywords to look for
            category_keywords = {
                'problem': 'Problem & Solution',
                'solution': 'Problem & Solution',
                'market': 'Market Opportunity',
                'opportunity': 'Market Opportunity',
                'business model': 'Business Model',
                'revenue': 'Business Model',
                'team': 'Team',
                'traction': 'Traction & Validation',
                'validation': 'Traction & Validation',
                'competition': 'Competitive Advantage',
                'competitive': 'Competitive Advantage',
                'financial': 'Financial Projections',
                'projections': 'Financial Projections'
            }
            
            for elem in category_elements:
                text = elem.get_text(strip=True)
                text_lower = text.lower()
                
                for keyword, category in category_keywords.items():
                    if keyword in text_lower and category not in detected_categories:
                        detected_categories.add(category)
            
            # If we found categories, use them
            if detected_categories:
                for cat in detected_categories:
                    features["analysis_categories"].append({
                        "name": cat,
                        "weight": 15  # Default weight
                    })
                
                # Adjust weights if we have specific categories
                if len(features["analysis_categories"]) > 0:
                    # Problem & Solution gets higher weight
                    for cat in features["analysis_categories"]:
                        if 'Problem' in cat["name"]:
                            cat["weight"] = 20
            
            # If scraping didn't work well, use defaults
            if not features["analysis_categories"] or len(features["analysis_categories"]) < 5:
                logger.info("Insufficient categories found, using defaults")
                features = self._get_default_features()
            
        except Exception as e:
            logger.warning(f"Error extracting features: {str(e)}")
            features = self._get_default_features()
        
        return features
    
    def _get_default_features(self) -> Dict:
        """Return default analysis features based on standard VC evaluation criteria"""
        return {
            "scraped_at": datetime.now().isoformat(),
            "source": "default",
            "analysis_categories": [
                {
                    "name": "Problem & Solution",
                    "weight": 20,
                    "description": "Clarity of problem definition and proposed solution"
                },
                {
                    "name": "Market Opportunity",
                    "weight": 15,
                    "description": "Market size, growth potential, and target market definition"
                },
                {
                    "name": "Business Model",
                    "weight": 15,
                    "description": "Revenue model, pricing strategy, and unit economics"
                },
                {
                    "name": "Competitive Advantage",
                    "weight": 15,
                    "description": "Unique value proposition and competitive positioning"
                },
                {
                    "name": "Traction & Validation",
                    "weight": 15,
                    "description": "Customer validation, growth metrics, and milestones"
                },
                {
                    "name": "Team",
                    "weight": 10,
                    "description": "Team experience, expertise, and completeness"
                },
                {
                    "name": "Financial Projections",
                    "weight": 10,
                    "description": "Financial forecasts, use of funds, and path to profitability"
                }
            ],
            "evaluation_criteria": [
                "Clarity and completeness of information",
                "Data quality and supporting evidence",
                "Persuasiveness and credibility",
                "Professional presentation and design",
                "Logical flow and storytelling",
                "Realistic assumptions and projections"
            ]
        }
    
    def _save_features(self, features: Dict):
        """Save scraped features to file"""
        with open(self.features_file, 'w', encoding='utf-8') as f:
            json.dump(features, f, indent=2)
        
        logger.info(f"Saved features to {self.features_file}")
    
    def load_features(self) -> Dict:
        """
        Load features from file or return defaults
        
        Returns:
            Analysis features dictionary
        """
        if self.features_file.exists():
            try:
                with open(self.features_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading features: {str(e)}")
        
        # Return defaults if file doesn't exist or can't be loaded
        return self._get_default_features()
    
    def update_features(self, updates: Dict) -> Dict:
        """
        Update features with custom values
        
        Args:
            updates: Dictionary with updates
            
        Returns:
            Updated features
        """
        features = self.load_features()
        
        # Update categories if provided
        if "analysis_categories" in updates:
            features["analysis_categories"] = updates["analysis_categories"]
        
        # Update criteria if provided
        if "evaluation_criteria" in updates:
            features["evaluation_criteria"] = updates["evaluation_criteria"]
        
        # Save updates
        features["updated_at"] = datetime.now().isoformat()
        self._save_features(features)
        
        return features