"""
Enhanced Report Generator for creating professional PDF reports
Modeled after Evalyze.ai assessment report structure
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, Image as RLImage, KeepTogether
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.pdfgen import canvas
from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

class NumberedCanvas(canvas.Canvas):
    """Custom canvas for page numbers and headers/footers"""
    
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_elements(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_elements(self, page_count):
        """Draw page number and footer"""
        self.setFont('Helvetica', 9)
        self.setFillColor(colors.HexColor('#7f8c8d'))
        
        # Page number at bottom center
        page_num = f"Page {self._pageNumber} / {page_count}"
        self.drawCentredString(letter[0] / 2, 30, page_num)
        
        # Footer line
        self.setStrokeColor(colors.HexColor('#ecf0f1'))
        self.setLineWidth(1)
        self.line(50, 40, letter[0] - 50, 40)


class ReportGenerator:
    """Generates professional PDF reports from pitch deck analysis"""
    
    def __init__(self, reports_dir: str = r"C:\coding\OrionEudverse\picth_desk\reports", logo_path: str =r"C:\coding\OrionEudverse\picth_desk\backend\logo.jpg"):
        """
        Initialize report generator
        
        Args:
            reports_dir: Directory to save reports (default: C:\coding\OrionEudverse\picth_desk\reports)
            logo_path: Path to company logo image (PNG, JPG)
        """
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Report generator initialized with directory: {self.reports_dir}")
        
        # Set logo path if provided and exists
        if logo_path:
            logo = Path(logo_path)
            self.logo_path = logo if logo.exists() else None
            if not self.logo_path:
                logger.warning(f"Logo file not found: {logo_path}")
        else:
            self.logo_path = None
    
    def generate_report(self, analysis_data: Dict, output_filename: str = None) -> str:
        """
        Generate a comprehensive PDF report
        
        Args:
            analysis_data: Analysis results from AIAnalyzer
            output_filename: Optional custom filename
            
        Returns:
            Path to generated PDF report
        """
        if not output_filename:
            analysis_id = analysis_data.get("id", "unknown")
            output_filename = f"{analysis_id}_report.pdf"
        
        output_path = self.reports_dir / output_filename
        
        logger.info(f"Generating report: {output_filename}")
        
        # Create PDF document with custom canvas
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=60,
            leftMargin=60,
            topMargin=60,
            bottomMargin=60,
        )
        
        # Build document content
        story = []
        styles = self._create_styles()
        
        # Cover Page
        story.extend(self._create_cover_page(analysis_data, styles))
        story.append(PageBreak())
        
        # Executive Summary Page
        story.extend(self._create_executive_summary(analysis_data, styles))
        story.append(PageBreak())
        
        # Overall Assessment Page
        story.extend(self._create_overall_assessment(analysis_data, styles))
        story.append(PageBreak())
        
        # Category Analysis Pages
        story.extend(self._create_category_analysis(analysis_data, styles))
        story.append(PageBreak())
        
        # Strengths and Weaknesses
        story.extend(self._create_strengths_weaknesses(analysis_data, styles))
        story.append(PageBreak())
        
        # Recommendations Page
        story.extend(self._create_recommendations(analysis_data, styles))
        
        # Build PDF with numbered pages
        doc.build(story, canvasmaker=NumberedCanvas)
        
        logger.info(f"Report generated successfully: {output_path}")
        return str(output_path)
    
    def _create_styles(self) -> Dict:
        """Create custom paragraph styles"""
        styles = getSampleStyleSheet()
        
        custom_styles = {
            'cover_title': ParagraphStyle(
                'CoverTitle',
                parent=styles['Heading1'],
                fontSize=36,
                textColor=colors.HexColor('#1a237e'),
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold',
                leading=42
            ),
            'cover_subtitle': ParagraphStyle(
                'CoverSubtitle',
                parent=styles['Normal'],
                fontSize=18,
                textColor=colors.HexColor('#5c6bc0'),
                spaceAfter=40,
                alignment=TA_CENTER,
                fontName='Helvetica',
                leading=24
            ),
            'section_title': ParagraphStyle(
                'SectionTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a237e'),
                spaceAfter=20,
                spaceBefore=10,
                fontName='Helvetica-Bold',
                borderWidth=0,
                borderPadding=0,
                borderColor=colors.HexColor('#5c6bc0'),
                leftIndent=0
            ),
            'subsection_title': ParagraphStyle(
                'SubsectionTitle',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#283593'),
                spaceAfter=12,
                spaceBefore=16,
                fontName='Helvetica-Bold'
            ),
            'category_title': ParagraphStyle(
                'CategoryTitle',
                parent=styles['Heading3'],
                fontSize=14,
                textColor=colors.HexColor('#1a237e'),
                spaceAfter=8,
                spaceBefore=12,
                fontName='Helvetica-Bold'
            ),
            'body': ParagraphStyle(
                'CustomBody',
                parent=styles['BodyText'],
                fontSize=11,
                leading=16,
                textColor=colors.HexColor('#37474f'),
                alignment=TA_JUSTIFY,
                spaceAfter=10
            ),
            'body_left': ParagraphStyle(
                'BodyLeft',
                parent=styles['BodyText'],
                fontSize=11,
                leading=16,
                textColor=colors.HexColor('#37474f'),
                alignment=TA_LEFT,
                spaceAfter=8
            ),
            'bullet': ParagraphStyle(
                'Bullet',
                parent=styles['BodyText'],
                fontSize=10,
                leading=14,
                textColor=colors.HexColor('#455a64'),
                leftIndent=20,
                spaceAfter=6
            ),
            'metadata': ParagraphStyle(
                'Metadata',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#78909c'),
                alignment=TA_CENTER
            )
        }
        
        return custom_styles
    
    def _create_cover_page(self, data: Dict, styles: Dict) -> List:
        """Create professional cover page"""
        elements = []
        
        # Add logo if available
        if self.logo_path:
            try:
                logo = RLImage(str(self.logo_path))
                aspect = logo.imageWidth / logo.imageHeight
                logo.drawHeight = 1.2 * inch
                logo.drawWidth = logo.drawHeight * aspect
                logo.hAlign = 'CENTER'
                elements.append(logo)
                elements.append(Spacer(1, 30))
            except Exception as e:
                logger.warning(f"Could not add logo: {str(e)}")
        
        # Spacer to center content
        elements.append(Spacer(1, 2 * inch))
        
        # Title
        elements.append(Paragraph(
            "PITCH DECK ANALYSIS REPORT",
            styles['cover_title']
        ))
        
        # Subtitle
        elements.append(Paragraph(
            "Comprehensive Investment Evaluation",
            styles['cover_subtitle']
        ))
        
        # Decorative line
        elements.append(self._create_colored_line(colors.HexColor('#5c6bc0'), 4))
        elements.append(Spacer(1, 40))
        
        # Document info box
        filename = data.get("filename", "Unknown")
        created_at = data.get("created_at", datetime.now().isoformat())
        overall_score = data.get('overall_score', 0)
        
        info_data = [
            ["Document", filename],
            ["Analysis Date", created_at.split('T')[0]],
            ["Overall Score", f"{overall_score:.1f} / 100"],
            ["Report Generated", datetime.now().strftime("%Y-%m-%d %H:%M")]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 3.5*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#283593')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#546e7a')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#cfd8dc')),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        elements.append(info_table)
        
        # Footer text
        elements.append(Spacer(1, 80))
        elements.append(Paragraph(
            "CONFIDENTIAL - AI-Powered Analysis",
            styles['metadata']
        ))
        
        return elements
    
    def _create_executive_summary(self, data: Dict, styles: Dict) -> List:
        """Create executive summary page"""
        elements = []
        
        # Section header
        elements.append(Paragraph("EXECUTIVE SUMMARY", styles['section_title']))
        elements.append(self._create_colored_line(colors.HexColor('#5c6bc0'), 2))
        elements.append(Spacer(1, 20))
        
        # Summary content
        summary = data.get("executive_summary", "No summary available")
        elements.append(Paragraph(summary, styles['body']))
        elements.append(Spacer(1, 30))
        
        # Key highlights box
        overall_score = data.get('overall_score', 0)
        rating = self._get_rating_label(overall_score)
        
        elements.append(Paragraph("Key Highlights", styles['subsection_title']))
        
        highlights_data = [
            ["Overall Assessment", f"{overall_score:.1f} / 100"],
            ["Rating", rating],
            ["Pages Analyzed", str(data.get('structure', {}).get('page_count', 'N/A'))],
            ["Word Count", f"{data.get('word_count', 0):,}"]
        ]
        
        highlights_table = Table(highlights_data, colWidths=[3*inch, 3*inch])
        highlights_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#283593')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#546e7a')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f7fa')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cfd8dc')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(highlights_table)
        
        return elements
    
    def _create_overall_assessment(self, data: Dict, styles: Dict) -> List:
        """Create overall assessment page with score visualization"""
        elements = []
        
        elements.append(Paragraph("OVERALL ASSESSMENT", styles['section_title']))
        elements.append(self._create_colored_line(colors.HexColor('#5c6bc0'), 2))
        elements.append(Spacer(1, 20))
        
        # Large score display
        overall_score = data.get('overall_score', 0)
        elements.append(self._create_large_score_card(overall_score))
        elements.append(Spacer(1, 30))
        
        # Category scores table
        elements.append(Paragraph("Performance by Category", styles['subsection_title']))
        elements.append(Spacer(1, 10))
        
        category_scores = data.get('category_scores', {})
        if category_scores:
            elements.append(self._create_category_scores_table(category_scores))
        
        return elements
    
    def _create_category_analysis(self, data: Dict, styles: Dict) -> List:
        """Create detailed category analysis pages"""
        elements = []
        
        elements.append(Paragraph("DETAILED CATEGORY ANALYSIS", styles['section_title']))
        elements.append(self._create_colored_line(colors.HexColor('#5c6bc0'), 2))
        elements.append(Spacer(1, 20))
        
        category_feedback = data.get('category_feedback', {})
        category_scores = data.get('category_scores', {})
        
        category_icons = {
            'problem': '🎯',
            'solution': '💡',
            'market': '📊',
            'business_model': '💰',
            'team': '👥',
            'traction': '🚀'
        }
        
        for i, (category, feedback) in enumerate(category_feedback.items()):
            score = category_scores.get(category, 0)
            icon = category_icons.get(category, '📋')
            
            # Category section
            category_elements = []
            
            # Category header with icon and score
            category_title = f"{icon} {category.replace('_', ' ').title()}"
            category_elements.append(Paragraph(category_title, styles['category_title']))
            
            # Score badge
            category_elements.append(self._create_score_badge(score))
            category_elements.append(Spacer(1, 12))
            
            # Analysis text
            analysis_text = feedback.get('analysis', 'No analysis available')
            category_elements.append(Paragraph(self._clean_text(analysis_text), styles['body']))
            category_elements.append(Spacer(1, 10))
            
            # Key points
            key_points = feedback.get('key_points', [])
            if key_points:
                category_elements.append(Paragraph("<b>Key Points:</b>", styles['body']))
                for point in key_points:
                    category_elements.append(Paragraph(
                        f"• {self._clean_text(point)}",
                        styles['bullet']
                    ))
                category_elements.append(Spacer(1, 10))
            
            # Wrap category section to keep together
            elements.append(KeepTogether(category_elements))
            elements.append(Spacer(1, 20))
            
            # Page break after every 2 categories
            if (i + 1) % 2 == 0 and (i + 1) < len(category_feedback):
                elements.append(PageBreak())
        
        return elements
    
    def _create_strengths_weaknesses(self, data: Dict, styles: Dict) -> List:
        """Create strengths and weaknesses page"""
        elements = []
        
        elements.append(Paragraph("STRENGTHS & AREAS FOR IMPROVEMENT", styles['section_title']))
        elements.append(self._create_colored_line(colors.HexColor('#5c6bc0'), 2))
        elements.append(Spacer(1, 20))
        
        # Strengths section
        elements.append(Paragraph("✓ Key Strengths", styles['subsection_title']))
        
        strengths = data.get('strengths', [])
        if strengths:
            strength_data = [[self._clean_text(s)] for s in strengths]
            strength_table = Table(strength_data, colWidths=[6*inch])
            strength_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2e7d32')),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8f5e9')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#c8e6c9')),
            ]))
            elements.append(strength_table)
        else:
            elements.append(Paragraph("No specific strengths identified.", styles['body']))
        
        elements.append(Spacer(1, 30))
        
        # Weaknesses section
        elements.append(Paragraph("⚠ Areas for Improvement", styles['subsection_title']))
        
        weaknesses = data.get('weaknesses', [])
        if weaknesses:
            weakness_data = [[self._clean_text(w)] for w in weaknesses]
            weakness_table = Table(weakness_data, colWidths=[6*inch])
            weakness_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#d84315')),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fbe9e7')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#ffccbc')),
            ]))
            elements.append(weakness_table)
        else:
            elements.append(Paragraph("No specific weaknesses identified.", styles['body']))
        
        return elements
    
    def _create_recommendations(self, data: Dict, styles: Dict) -> List:
        """Create recommendations page"""
        elements = []
        
        elements.append(Paragraph("STRATEGIC RECOMMENDATIONS", styles['section_title']))
        elements.append(self._create_colored_line(colors.HexColor('#5c6bc0'), 2))
        elements.append(Spacer(1, 20))
        
        recommendations = data.get('recommendations', [])
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                rec_data = [[f"{i}.", self._clean_text(rec)]]
                rec_table = Table(rec_data, colWidths=[0.4*inch, 5.6*inch])
                rec_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, 0), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 11),
                    ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#1a237e')),
                    ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#37474f')),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f7fa')),
                    ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                    ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cfd8dc')),
                ]))
                elements.append(rec_table)
                elements.append(Spacer(1, 12))
        else:
            elements.append(Paragraph("No specific recommendations available.", styles['body']))
        
        return elements
    
    def _create_colored_line(self, color, width: int = 2) -> Table:
        """Create a colored horizontal line"""
        data = [['']]
        table = Table(data, colWidths=[6.5*inch])
        table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), width, color),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        return table
    
    def _get_rating_label(self, score: float) -> str:
        """Get rating label based on score"""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Very Good"
        elif score >= 70:
            return "Good"
        elif score >= 60:
            return "Fair"
        elif score >= 50:
            return "Promising"
        else:
            return "Needs Improvement"
    
    def _get_rating_color(self, score: float) -> tuple:
        """Get color scheme based on score"""
        if score >= 80:
            return colors.HexColor('#2e7d32'), colors.HexColor('#e8f5e9')
        elif score >= 70:
            return colors.HexColor('#1976d2'), colors.HexColor('#e3f2fd')
        elif score >= 60:
            return colors.HexColor('#0288d1'), colors.HexColor('#e1f5fe')
        elif score >= 50:
            return colors.HexColor('#f57c00'), colors.HexColor('#fff3e0')
        else:
            return colors.HexColor('#d32f2f'), colors.HexColor('#ffebee')
    
    def _create_large_score_card(self, score: float) -> Table:
        """Create large score display card"""
        rating = self._get_rating_label(score)
        color, bg_color = self._get_rating_color(score)
        
        data = [
            ["Overall Score", ""],
            [f"{score:.1f}", "/ 100"],
            [rating, ""]
        ]
        
        table = Table(data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (1, 0), 14),
            ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (0, 1), 56),
            ('FONTNAME', (1, 1), (1, 1), 'Helvetica'),
            ('FONTSIZE', (1, 1), (1, 1), 24),
            ('FONTNAME', (0, 2), (0, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 2), (0, 2), 18),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.HexColor('#546e7a')),
            ('TEXTCOLOR', (0, 1), (1, 1), color),
            ('TEXTCOLOR', (0, 2), (0, 2), color),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (0, 1), 'RIGHT'),
            ('ALIGN', (1, 1), (1, 1), 'LEFT'),
            ('ALIGN', (0, 2), (1, 2), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('SPAN', (0, 0), (1, 0)),
            ('SPAN', (0, 2), (1, 2)),
            ('BOX', (0, 0), (-1, -1), 3, color),
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
            ('TOPPADDING', (0, 0), (-1, -1), 20),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
        ]))
        
        return table
    
    def _create_score_badge(self, score: float) -> Table:
        """Create small score badge"""
        rating = self._get_rating_label(score)
        color, bg_color = self._get_rating_color(score)
        
        data = [[f"Score: {score:.0f}/100 — {rating}"]]
        
        table = Table(data, colWidths=[3.5*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 11),
            ('TEXTCOLOR', (0, 0), (0, 0), color),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('BACKGROUND', (0, 0), (0, 0), bg_color),
            ('BOX', (0, 0), (0, 0), 1.5, color),
            ('TOPPADDING', (0, 0), (0, 0), 6),
            ('BOTTOMPADDING', (0, 0), (0, 0), 6),
            ('LEFTPADDING', (0, 0), (0, 0), 12),
            ('RIGHTPADDING', (0, 0), (0, 0), 12),
        ]))
        
        return table
    
    def _create_category_scores_table(self, category_scores: Dict) -> Table:
        """Create professional category scores table"""
        
        # Prepare data with header
        data = [["Category", "Score", "Rating", "Performance"]]
        
        for category, score in sorted(category_scores.items(), key=lambda x: x[1], reverse=True):
            # Create visual bar
            bar_length = int(score / 5)
            bar = "█" * bar_length
            
            # Get rating
            rating = self._get_rating_label(score)
            
            data.append([
                category.replace('_', ' ').title(),
                f"{score:.1f}",
                rating,
                bar
            ])
        
        table = Table(data, colWidths=[2.2*inch, 0.8*inch, 1.3*inch, 1.7*inch])
        
        # Build style
        style_commands = [
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('ALIGN', (3, 0), (3, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cfd8dc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f7fa')]),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]
        
        # Add colored backgrounds for ratings
        for i, (category, score) in enumerate(sorted(category_scores.items(), key=lambda x: x[1], reverse=True), 1):
            color, bg_color = self._get_rating_color(score)
            style_commands.append(('BACKGROUND', (2, i), (2, i), bg_color))
            style_commands.append(('TEXTCOLOR', (2, i), (2, i), color))
            style_commands.append(('TEXTCOLOR', (3, i), (3, i), color))
        
        table.setStyle(TableStyle(style_commands))
        
        return table
    
    def _clean_text(self, text: str) -> str:
        """Clean text by removing markdown formatting"""
        if not text:
            return ""
        
        # Remove markdown bold
        text = text.replace('**', '')
        # Remove markdown italic
        text = text.replace('*', '')
        # Remove markdown headers
        text = text.replace('###', '').replace('##', '').replace('#', '')
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text