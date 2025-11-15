"""
Example usage of the Pitch Deck Analyzer
Demonstrates how to use each module independently
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Import modules
from pdf_processor import PDFProcessor
from ai_analyzer import AIAnalyzer
from report_generator import ReportGenerator
from database import AnalysisDatabase
from evalyze_scraper import EvalyzeScraper

# Load environment
load_dotenv()

def example_1_process_pdf():
    """Example: Process a PDF and extract content"""
    print("\n=== Example 1: PDF Processing ===")
    
    processor = PDFProcessor()
    
    # Process a sample PDF
    pdf_path = "../samples/sample_pitch.pdf"
    
    if not Path(pdf_path).exists():
        print(f"Sample PDF not found at {pdf_path}")
        print("Please add a sample PDF to the samples/ directory")
        return None
    
    extracted_data = processor.process_pdf(pdf_path)
    
    print(f"Filename: {extracted_data['filename']}")
    print(f"Page Count: {extracted_data['page_count']}")
    print(f"Word Count: {extracted_data['word_count']}")
    print(f"Text Preview: {extracted_data['text_content'][:200]}...")
    
    return extracted_data

def example_2_scrape_features():
    """Example: Scrape Evalyze features"""
    print("\n=== Example 2: Scraping Evalyze Features ===")
    
    scraper = EvalyzeScraper()
    
    # Scrape features (will use defaults if scraping fails)
    features = scraper.scrape_features()
    
    print(f"Scraped at: {features['scraped_at']}")
    print(f"Number of categories: {len(features['analysis_categories'])}")
    
    print("\nCategories:")
    for cat in features['analysis_categories']:
        print(f"  - {cat['name']} (weight: {cat['weight']})")
    
    return features

def example_3_analyze_pitch():
    """Example: Complete analysis pipeline"""
    print("\n=== Example 3: Complete Analysis ===")
    
    # Step 1: Process PDF
    processor = PDFProcessor()
    pdf_path = "../samples/sample_pitch.pdf"
    
    if not Path(pdf_path).exists():
        print(f"Sample PDF not found at {pdf_path}")
        return
    
    print("Processing PDF...")
    extracted_data = processor.process_pdf(pdf_path)
    
    # Step 2: Analyze with AI
    print("Analyzing with AI...")
    analyzer = AIAnalyzer(
        api_key=os.getenv("GEMINI_API_KEY"),
        features_file="../data/evalyze_features.json"
    )
    
    analysis_results = analyzer.analyze_pitch_deck(extracted_data)
    
    # Step 3: Print results
    print(f"\n--- Analysis Results ---")
    print(f"Overall Score: {analysis_results['overall_score']:.1f}/100")
    print(f"\nCategory Scores:")
    for category, score in analysis_results['category_scores'].items():
        print(f"  {category}: {score:.1f}/100")
    
    print(f"\nExecutive Summary:")
    print(f"  {analysis_results['executive_summary']}")
    
    print(f"\nTop 3 Strengths:")
    for i, strength in enumerate(analysis_results['strengths'][:3], 1):
        print(f"  {i}. {strength}")
    
    print(f"\nTop 3 Weaknesses:")
    for i, weakness in enumerate(analysis_results['weaknesses'][:3], 1):
        print(f"  {i}. {weakness}")
    
    return analysis_results

def example_4_save_to_database():
    """Example: Save analysis to database"""
    print("\n=== Example 4: Database Storage ===")
    
    # Run analysis first
    processor = PDFProcessor()
    analyzer = AIAnalyzer(api_key=os.getenv("GEMINI_API_KEY"))
    db = AnalysisDatabase()
    
    pdf_path = "../samples/sample_pitch.pdf"
    
    if not Path(pdf_path).exists():
        print(f"Sample PDF not found at {pdf_path}")
        return
    
    # Process and analyze
    extracted_data = processor.process_pdf(pdf_path)
    analysis_results = analyzer.analyze_pitch_deck(extracted_data)
    analysis_results["filename"] = "sample_pitch.pdf"
    
    # Save to database
    analysis_id = db.save_analysis(analysis_results)
    print(f"Analysis saved with ID: {analysis_id}")
    
    # Retrieve it
    retrieved = db.get_analysis(analysis_id)
    print(f"Retrieved analysis for: {retrieved['filename']}")
    
    # List all analyses
    all_analyses = db.list_analyses(limit=5)
    print(f"\nTotal analyses in database: {len(all_analyses)}")
    for analysis in all_analyses[:3]:
        print(f"  - {analysis['filename']} (Score: {analysis['score']:.1f})")
    
    return analysis_id

def example_5_generate_report():
    """Example: Generate PDF report"""
    print("\n=== Example 5: Report Generation ===")
    
    # Run full pipeline
    processor = PDFProcessor()
    analyzer = AIAnalyzer(api_key=os.getenv("GEMINI_API_KEY"))
    db = AnalysisDatabase()
    report_gen = ReportGenerator()
    
    pdf_path = "../samples/sample_pitch.pdf"
    
    if not Path(pdf_path).exists():
        print(f"Sample PDF not found at {pdf_path}")
        return
    
    # Process, analyze, and save
    print("Processing and analyzing...")
    extracted_data = processor.process_pdf(pdf_path)
    analysis_results = analyzer.analyze_pitch_deck(extracted_data)
    analysis_results["filename"] = "sample_pitch.pdf"
    
    analysis_id = db.save_analysis(analysis_results)
    
    # Generate report
    print("Generating PDF report...")
    report_path = report_gen.generate_report(
        db.get_analysis(analysis_id)
    )
    
    print(f"Report generated at: {report_path}")
    
    return report_path

def example_6_export_training_data():
    """Example: Export data for training"""
    print("\n=== Example 6: Export Training Data ===")
    
    db = AnalysisDatabase()
    
    export_path = db.export_for_training()
    print(f"Training data exported to: {export_path}")
    
    # Show statistics
    stats = db.get_statistics()
    print(f"\nDatabase Statistics:")
    print(f"  Total Analyses: {stats['total_analyses']}")
    print(f"  Average Score: {stats['average_score']:.1f}")
    print(f"  Highest Score: {stats['highest_score']:.1f}")
    print(f"  Lowest Score: {stats['lowest_score']:.1f}")
    
    return export_path

def run_all_examples():
    """Run all examples"""
    print("=" * 60)
    print("PITCH DECK ANALYZER - EXAMPLE USAGE")
    print("=" * 60)
    
    try:
        # Check for API key
        if not os.getenv("GEMINI_API_KEY"):
            print("\n⚠️  WARNING: GEMINI_API_KEY not found in environment")
            print("Please set your Gemini API key in .env file")
            return
        
        # Run examples that don't require API
        example_1_process_pdf()
        example_2_scrape_features()
        
        # Run examples that require API
        print("\n" + "=" * 60)
        print("Running AI-powered examples (requires API key)...")
        print("=" * 60)
        
        example_3_analyze_pitch()
        example_4_save_to_database()
        example_5_generate_report()
        example_6_export_training_data()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Create necessary directories
    Path("../samples").mkdir(exist_ok=True)
    Path("../data").mkdir(exist_ok=True)
    Path("../reports").mkdir(exist_ok=True)
    Path("../logs").mkdir(exist_ok=True)
    
    # Run all examples
    run_all_examples()
    
    # Or run individual examples:
    # example_1_process_pdf()
    # example_2_scrape_features()
    # example_3_analyze_pitch()
    # example_4_save_to_database()
    # example_5_generate_report()
    # example_6_export_training_data()