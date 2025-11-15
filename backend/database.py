"""
Database Module for storing and retrieving pitch deck analyses
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)

class AnalysisDatabase:
    """Manages storage and retrieval of pitch deck analyses"""
    
    def __init__(self, data_dir: str = "../data"):
        """
        Initialize database
        
        Args:
            data_dir: Directory for storing data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Individual analyses directory
        self.analyses_dir = self.data_dir / "analyses"
        self.analyses_dir.mkdir(exist_ok=True)
        
        # Main database file
        self.db_file = self.data_dir / "analyses.json"
        
        # Initialize database if it doesn't exist
        if not self.db_file.exists():
            self._initialize_database()
    
    def _initialize_database(self):
        """Initialize empty database file"""
        initial_data = {
            "analyses": [],
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2)
        
        logger.info("Initialized new database")
    
    def save_analysis(self, analysis_data: Dict) -> str:
        """
        Save a new analysis to database
        
        Args:
            analysis_data: Complete analysis results
            
        Returns:
            Unique analysis ID
        """
        # Generate unique ID
        analysis_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Add metadata
        analysis_data["id"] = analysis_id
        analysis_data["created_at"] = timestamp
        
        # Save individual analysis file
        analysis_file = self.analyses_dir / f"{analysis_id}.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2)
        
        # Update main database
        db_data = self._load_database()
        
        # Add summary to main database
        summary = {
            "id": analysis_id,
            "filename": analysis_data.get("filename", "Unknown"),
            "score": analysis_data.get("overall_score", 0),
            "created_at": timestamp,
            "file_path": str(analysis_file)
        }
        
        db_data["analyses"].append(summary)
        
        # Save updated database
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(db_data, f, indent=2)
        
        logger.info(f"Saved analysis: {analysis_id}")
        return analysis_id
    
    def get_analysis(self, analysis_id: str) -> Optional[Dict]:
        """
        Retrieve an analysis by ID
        
        Args:
            analysis_id: Unique analysis identifier
            
        Returns:
            Complete analysis data or None if not found
        """
        analysis_file = self.analyses_dir / f"{analysis_id}.json"
        
        if not analysis_file.exists():
            logger.warning(f"Analysis not found: {analysis_id}")
            return None
        
        try:
            with open(analysis_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading analysis {analysis_id}: {str(e)}")
            return None
    
    def list_analyses(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        List all analyses with pagination
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of analysis summaries
        """
        db_data = self._load_database()
        analyses = db_data.get("analyses", [])
        
        # Sort by creation date (newest first)
        analyses.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Apply pagination
        return analyses[offset:offset + limit]
    
    def delete_analysis(self, analysis_id: str) -> bool:
        """
        Delete an analysis
        
        Args:
            analysis_id: Unique analysis identifier
            
        Returns:
            True if deleted, False if not found
        """
        analysis_file = self.analyses_dir / f"{analysis_id}.json"
        
        if not analysis_file.exists():
            return False
        
        try:
            # Delete individual file
            analysis_file.unlink()
            
            # Update main database
            db_data = self._load_database()
            db_data["analyses"] = [
                a for a in db_data["analyses"] 
                if a.get("id") != analysis_id
            ]
            
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(db_data, f, indent=2)
            
            logger.info(f"Deleted analysis: {analysis_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting analysis {analysis_id}: {str(e)}")
            return False
    
    def search_analyses(self, query: str, field: str = "filename") -> List[Dict]:
        """
        Search analyses by field
        
        Args:
            query: Search query
            field: Field to search in (filename, id, etc.)
            
        Returns:
            List of matching analyses
        """
        db_data = self._load_database()
        analyses = db_data.get("analyses", [])
        
        query_lower = query.lower()
        
        results = [
            a for a in analyses 
            if query_lower in str(a.get(field, "")).lower()
        ]
        
        return results
    
    def get_statistics(self) -> Dict:
        """
        Get database statistics
        
        Returns:
            Dictionary with statistics
        """
        db_data = self._load_database()
        analyses = db_data.get("analyses", [])
        
        if not analyses:
            return {
                "total_analyses": 0,
                "average_score": 0,
                "highest_score": 0,
                "lowest_score": 0
            }
        
        scores = [a.get("score", 0) for a in analyses]
        
        return {
            "total_analyses": len(analyses),
            "average_score": sum(scores) / len(scores) if scores else 0,
            "highest_score": max(scores) if scores else 0,
            "lowest_score": min(scores) if scores else 0,
            "date_range": {
                "earliest": min(a.get("created_at", "") for a in analyses),
                "latest": max(a.get("created_at", "") for a in analyses)
            }
        }
    
    def export_for_training(self, output_file: str = None) -> str:
        """
        Export all analyses for ML training
        
        Args:
            output_file: Optional output file path
            
        Returns:
            Path to export file
        """
        if not output_file:
            output_file = self.data_dir / "training_export.json"
        else:
            output_file = Path(output_file)
        
        # Load all analyses
        db_data = self._load_database()
        analyses = db_data.get("analyses", [])
        
        training_data = []
        
        for analysis_summary in analyses:
            analysis_id = analysis_summary.get("id")
            full_analysis = self.get_analysis(analysis_id)
            
            if full_analysis:
                # Extract relevant data for training
                training_item = {
                    "id": analysis_id,
                    "input": {
                        "text": full_analysis.get("extracted_text", ""),
                        "metadata": full_analysis.get("metadata", {})
                    },
                    "output": {
                        "overall_score": full_analysis.get("overall_score", 0),
                        "category_scores": full_analysis.get("category_scores", {}),
                        "category_feedback": full_analysis.get("category_feedback", {}),
                        "strengths": full_analysis.get("strengths", []),
                        "weaknesses": full_analysis.get("weaknesses", []),
                        "recommendations": full_analysis.get("recommendations", [])
                    },
                    "created_at": full_analysis.get("created_at", "")
                }
                
                training_data.append(training_item)
        
        # Save training export
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "export_date": datetime.now().isoformat(),
                "total_samples": len(training_data),
                "data": training_data
            }, f, indent=2)
        
        logger.info(f"Exported {len(training_data)} analyses for training to {output_file}")
        return str(output_file)
    
    def _load_database(self) -> Dict:
        """Load main database file"""
        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading database: {str(e)}")
            return {"analyses": []}
    
    def backup_database(self, backup_dir: str = None) -> str:
        """
        Create a backup of the entire database
        
        Args:
            backup_dir: Directory for backup (optional)
            
        Returns:
            Path to backup file
        """
        if not backup_dir:
            backup_dir = self.data_dir / "backups"
        else:
            backup_dir = Path(backup_dir)
        
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"backup_{timestamp}.json"
        
        # Load all data
        db_data = self._load_database()
        
        # Create complete backup
        backup_data = {
            "backup_date": datetime.now().isoformat(),
            "database": db_data,
            "analyses": []
        }
        
        # Include all individual analyses
        for analysis_summary in db_data.get("analyses", []):
            analysis_id = analysis_summary.get("id")
            full_analysis = self.get_analysis(analysis_id)
            if full_analysis:
                backup_data["analyses"].append(full_analysis)
        
        # Save backup
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2)
        
        logger.info(f"Created database backup: {backup_file}")
        return str(backup_file)