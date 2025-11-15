"""
FastAPI Main Application for Pitch Deck Analyzer
Updated to properly handle PDF downloads from backend
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import logging
from pathlib import Path
import os
from dotenv import load_dotenv
import json

# Import custom modules
from pdf_processor import PDFProcessor
from ai_analyzer import AIAnalyzer
from report_generator import ReportGenerator
from database import AnalysisDatabase
from evalyze_scraper import EvalyzeScraper

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Pitch Deck Analyzer API",
    description="AI-powered pitch deck analysis using Gemini - Returns PDF reports",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
pdf_processor = PDFProcessor()

# Get logo path from environment or use default
LOGO_PATH = os.getenv("COMPANY_LOGO_PATH", None)

ai_analyzer = AIAnalyzer(
    api_key=os.getenv("GEMINI_API_KEY"),
    features_file="../data/evalyze_features.json"
)
report_generator = ReportGenerator(
    reports_dir=r"C:\coding\OrionEudverse\picth_desk\reports",
    logo_path=LOGO_PATH
)
database = AnalysisDatabase(data_dir="../data")
scraper = EvalyzeScraper(data_dir="../data")

# Create necessary directories
Path("../logs").mkdir(exist_ok=True)
Path("../temp").mkdir(exist_ok=True)
Path("../data").mkdir(exist_ok=True)
Path("../data/analyses").mkdir(exist_ok=True)
Path(r"C:\coding\OrionEudverse\picth_desk\reports").mkdir(exist_ok=True)

# Pydantic models
class AnalysisMetadata(BaseModel):
    analysis_id: str
    filename: str
    overall_score: float
    created_at: str
    report_path: str

class AnalysisListItem(BaseModel):
    id: str
    filename: str
    score: float
    created_at: str

# API Routes

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Pitch Deck Analyzer API v2.0",
        "version": "2.0.0",
        "description": "AI-powered pitch deck analysis - Returns PDF reports",
        "endpoints": {
            "analyze_get_pdf": "POST /api/analyze (returns PDF)",
            "analyze_get_json": "POST /api/analyze-json (returns JSON)",
            "download_report": "GET /api/report/{analysis_id}",
            "get_analysis_data": "GET /api/analysis/{analysis_id}",
            "list_analyses": "GET /api/analyses",
            "statistics": "GET /api/statistics"
        },
        "logo_configured": LOGO_PATH is not None
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    reports_dir = Path(r"C:\coding\OrionEudverse\picth_desk\reports")
    return {
        "status": "healthy", 
        "service": "pitch-deck-analyzer",
        "version": "2.0.0",
        "logo_enabled": LOGO_PATH is not None,
        "reports_dir": str(reports_dir),
        "reports_dir_exists": reports_dir.exists(),
        "reports_dir_writable": os.access(reports_dir, os.W_OK) if reports_dir.exists() else False
    }

@app.get("/api/test-report/{analysis_id}")
async def test_report_exists(analysis_id: str):
    """Test endpoint to check if a report exists"""
    report_path = Path(r"C:\coding\OrionEudverse\picth_desk\reports") / f"{analysis_id}_report.pdf"
    
    return {
        "analysis_id": analysis_id,
        "report_path": str(report_path),
        "exists": report_path.exists(),
        "size": report_path.stat().st_size if report_path.exists() else 0,
        "readable": os.access(report_path, os.R_OK) if report_path.exists() else False
    }

@app.get("/api/latest-report")
async def get_latest_report():
    """Get the most recently generated report"""
    reports_dir = Path(r"C:\coding\OrionEudverse\picth_desk\reports")
    
    if not reports_dir.exists():
        raise HTTPException(status_code=404, detail="Reports directory not found")
    
    # Get all PDF files
    pdf_files = list(reports_dir.glob("*_report.pdf"))
    
    if not pdf_files:
        raise HTTPException(status_code=404, detail="No reports found")
    
    # Sort by modification time (most recent first)
    latest_report = max(pdf_files, key=lambda p: p.stat().st_mtime)
    
    # Extract analysis ID from filename
    analysis_id = latest_report.stem.replace('_report', '')
    
    logger.info(f"Serving latest report: {latest_report}")
    
    return FileResponse(
        path=latest_report,
        media_type="application/pdf",
        filename=f"latest_pitch_deck_analysis.pdf",
        headers={
            "X-Analysis-ID": analysis_id,
            "Content-Disposition": f'attachment; filename="latest_pitch_deck_analysis.pdf"'
        }
    )

@app.post("/api/analyze")
async def analyze_pitch_deck_pdf(
    file: UploadFile = File(...),
    return_json: bool = Query(False, description="Return JSON instead of PDF")
):
    """
    Analyze a pitch deck PDF and return the report PDF directly
    
    Args:
        file: PDF file upload
        return_json: If True, return JSON response instead of PDF
        
    Returns:
        PDF report file (default) or JSON with metadata
    """
    # Validate file
    if not file.filename.endswith('.pdf'):
        logger.error(f"Invalid file type: {file.filename}")
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    if file.size and file.size > 10 * 1024 * 1024:  # 10MB limit
        logger.error(f"File too large: {file.size} bytes")
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
    
    logger.info(f"========== NEW ANALYSIS REQUEST ==========")
    logger.info(f"Received file for analysis: {file.filename}")
    logger.info(f"Return JSON: {return_json}")
    
    try:
        # Read file content
        logger.info("Reading file content...")
        content = await file.read()
        logger.info(f"File content read: {len(content)} bytes")
        
        # Process PDF
        logger.info("Processing PDF...")
        extracted_data = pdf_processor.process_pdf_bytes(content, file.filename)
        logger.info(f"PDF processed successfully. Pages extracted: {len(extracted_data.get('pages', []))}")
        
        # Analyze with AI
        logger.info("Analyzing with AI...")
        analysis_results = ai_analyzer.analyze_pitch_deck(extracted_data)
        logger.info(f"AI analysis complete. Overall score: {analysis_results.get('overall_score')}")
        
        # Add filename
        analysis_results["filename"] = file.filename
        
        # Save to database
        logger.info("Saving to database...")
        analysis_id = database.save_analysis(analysis_results)
        logger.info(f"Analysis saved with ID: {analysis_id}")
        
        # Save JSON analysis to analyses folder
        logger.info("Saving JSON to analyses folder...")
        analyses_path = Path("../data/analyses") / f"{analysis_id}.json"
        with open(analyses_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False)
        logger.info(f"JSON saved to: {analyses_path}")
        
        # Generate report
        logger.info("Generating PDF report...")
        report_path = report_generator.generate_report(
            database.get_analysis(analysis_id)
        )
        logger.info(f"Report generation returned path: {report_path}")
        
        # Verify report exists
        report_file = Path(report_path)
        if not report_file.exists():
            logger.error(f"CRITICAL: Report file not found at {report_path}")
            raise HTTPException(
                status_code=500, 
                detail=f"Report generation failed - file not created at {report_path}"
            )
        
        report_size = report_file.stat().st_size
        logger.info(f"Report file verified: {report_path} ({report_size} bytes)")
        
        logger.info(f"========== ANALYSIS COMPLETED: {analysis_id} ==========")
        
        # Return PDF or JSON based on query parameter
        if return_json:
            logger.info("Returning JSON response")
            return {
                "status": "success",
                "analysis_id": analysis_id,
                "filename": file.filename,
                "overall_score": analysis_results["overall_score"],
                "report_url": f"/api/report/{analysis_id}",
                "analysis_url": f"/api/analysis/{analysis_id}",
                "message": "Analysis completed. Download report from report_url"
            }
        else:
            # Return PDF directly with proper headers for download
            logger.info(f"Returning PDF file: {report_path}")
            
            # Verify file exists and is readable
            report_file = Path(report_path)
            if not report_file.exists():
                logger.error(f"Report file not found after verification: {report_path}")
                raise HTTPException(
                    status_code=500, 
                    detail="Report file disappeared after generation"
                )
            
            file_size = report_file.stat().st_size
            logger.info(f"Sending PDF file: {file_size} bytes")
            
            return FileResponse(
                path=str(report_path),
                media_type="application/pdf",
                filename=f"pitch_analysis_{file.filename.replace('.pdf', '')}.pdf",
                headers={
                    "X-Analysis-ID": analysis_id,
                    "X-Overall-Score": str(analysis_results["overall_score"]),
                    "Access-Control-Expose-Headers": "X-Analysis-ID, X-Overall-Score, Content-Length",
                    "Cache-Control": "no-cache",
                    "Content-Length": str(file_size)
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"========== ANALYSIS FAILED ==========")
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/analyze-json")
async def analyze_pitch_deck_json(file: UploadFile = File(...)):
    """
    Analyze a pitch deck and return JSON response with metadata
    (Alternative endpoint that always returns JSON)
    
    Args:
        file: PDF file upload
        
    Returns:
        JSON with analysis metadata and download links
    """
    return await analyze_pitch_deck_pdf(file, return_json=True)

@app.get("/api/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """
    Get complete analysis results by ID (JSON)
    
    Args:
        analysis_id: Unique analysis identifier
        
    Returns:
        Complete analysis data in JSON
    """
    analysis = database.get_analysis(analysis_id)
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis

@app.get("/api/report/{analysis_id}")
async def download_report(analysis_id: str):
    """
    Download PDF report for an analysis
    
    Args:
        analysis_id: Unique analysis identifier
        
    Returns:
        PDF file for download
    """
    report_path = Path(r"C:\coding\OrionEudverse\picth_desk\reports") / f"{analysis_id}_report.pdf"
    
    if not report_path.exists():
        logger.error(f"Report not found: {report_path}")
        raise HTTPException(status_code=404, detail="Report not found")
    
    logger.info(f"Serving report for download: {report_path}")
    
    return FileResponse(
        path=report_path,
        media_type="application/pdf",
        filename=f"pitch_deck_analysis_{analysis_id}.pdf",
        headers={
            "Content-Disposition": f'attachment; filename="pitch_deck_analysis_{analysis_id}.pdf"'
        }
    )

@app.get("/api/analyses")
async def list_analyses(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List all analyses with pagination
    
    Args:
        limit: Maximum number of results (1-100)
        offset: Number of results to skip
        
    Returns:
        List of analysis summaries
    """
    analyses = database.list_analyses(limit=limit, offset=offset)
    return {
        "analyses": analyses, 
        "count": len(analyses),
        "limit": limit,
        "offset": offset
    }

@app.get("/api/analyses-files")
async def list_analyses_files():
    """
    List all JSON files in the analyses folder
    
    Returns:
        List of available analysis JSON files
    """
    analyses_dir = Path("../data/analyses")
    
    if not analyses_dir.exists():
        return {"files": [], "total": 0}
    
    files = []
    for file_path in analyses_dir.glob("*.json"):
        try:
            stat = file_path.stat()
            # Try to read basic info from file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                filename = data.get('filename', file_path.name)
                score = data.get('overall_score', 0)
            
            files.append({
                "filename": filename,
                "analysis_id": file_path.stem,
                "score": score,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "json_url": f"/api/analyses/{file_path.stem}",
                "report_url": f"/api/report/{file_path.stem}"
            })
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
    
    # Sort by creation time (newest first)
    files.sort(key=lambda x: x['created'], reverse=True)
    
    return {"files": files, "total": len(files)}

@app.get("/api/analyses/{analysis_id}")
async def get_analyses_json(analysis_id: str):
    """
    Get analysis JSON file from analyses folder
    
    Args:
        analysis_id: Unique analysis identifier (with or without .json)
        
    Returns:
        JSON analysis file
    """
    if not analysis_id.endswith('.json'):
        analysis_id = f"{analysis_id}.json"
    
    file_path = Path("../data/analyses") / analysis_id
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404, 
            detail="Analysis JSON file not found"
        )
    
    return FileResponse(
        path=file_path,
        media_type="application/json",
        filename=analysis_id
    )

@app.delete("/api/analysis/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """
    Delete an analysis and all associated files
    
    Args:
        analysis_id: Unique analysis identifier
        
    Returns:
        Success message
    """
    success = database.delete_analysis(analysis_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Delete report if exists
    report_path = Path(r"C:\coding\OrionEudverse\picth_desk\reports") / f"{analysis_id}_report.pdf"
    if report_path.exists():
        report_path.unlink()
        logger.info(f"Deleted report: {report_path}")
    
    # Delete JSON from analyses folder if exists
    analyses_path = Path("../data/analyses") / f"{analysis_id}.json"
    if analyses_path.exists():
        analyses_path.unlink()
        logger.info(f"Deleted analysis JSON: {analyses_path}")
    
    return {"message": "Analysis deleted successfully", "analysis_id": analysis_id}

@app.get("/api/statistics")
async def get_statistics():
    """
    Get database statistics
    
    Returns:
        Statistics about all analyses
    """
    stats = database.get_statistics()
    
    # Add analyses folder statistics
    analyses_dir = Path("../data/analyses")
    if analyses_dir.exists():
        json_files = list(analyses_dir.glob("*.json"))
        stats["analyses_folder"] = {
            "total_files": len(json_files),
            "path": str(analyses_dir.absolute())
        }
    
    # Add logo configuration
    stats["logo_configured"] = LOGO_PATH is not None
    if LOGO_PATH:
        stats["logo_path"] = LOGO_PATH
    
    return stats

@app.post("/api/scrape-features")
async def scrape_evalyze_features(url: Optional[str] = None):
    """
    Scrape Evalyze.ai to extract analysis features
    
    Args:
        url: Optional custom URL to scrape
        
    Returns:
        Scraped features
    """
    try:
        logger.info("Scraping Evalyze features...")
        features = scraper.scrape_features(url)
        return {"status": "success", "features": features}
    except Exception as e:
        logger.error(f"Error scraping features: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Scraping failed: {str(e)}"
        )

@app.get("/api/features")
async def get_features():
    """
    Get currently loaded analysis features
    
    Returns:
        Analysis features and criteria
    """
    features = scraper.load_features()
    return features

@app.post("/api/export-training-data")
async def export_training_data():
    """
    Export all analyses as training data
    
    Returns:
        Download link for training export
    """
    try:
        export_path = database.export_for_training()
        return {
            "status": "success",
            "export_path": export_path,
            "message": "Training data exported successfully",
            "download_url": f"/api/download/training-export"
        }
    except Exception as e:
        logger.error(f"Error exporting training data: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Export failed: {str(e)}"
        )

@app.put("/api/logo")
async def update_logo(logo_path: str):
    """
    Update the company logo path
    
    Args:
        logo_path: Path to new logo file
        
    Returns:
        Success message
    """
    global report_generator
    
    logo = Path(logo_path)
    if not logo.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"Logo file not found: {logo_path}"
        )
    
    # Reinitialize report generator with new logo
    report_generator = ReportGenerator(
        reports_dir=r"C:\coding\OrionEudverse\picth_desk\reports",
        logo_path=logo_path
    )
    
    return {
        "status": "success",
        "message": "Logo updated successfully",
        "logo_path": logo_path
    }

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    
    # Ensure directories exist
    Path("../logs").mkdir(exist_ok=True)
    Path("../temp").mkdir(exist_ok=True)
    Path("../data").mkdir(exist_ok=True)
    Path("../data/analyses").mkdir(exist_ok=True)
    Path(r"C:\coding\OrionEudverse\picth_desk\reports").mkdir(exist_ok=True)
    
    # Run server
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=os.getenv("DEBUG", "True").lower() == "true"
    )