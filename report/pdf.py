"""
OpsPilot++ PDF Report Generator

Creates professional PDF reports using ReportLab with:
- Professional styling and layout
- Charts and visualizations
- Comprehensive data presentation
- Branded design elements
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, KeepTogether
    )
    from reportlab.platypus.flowables import HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.graphics.shapes import Drawing, Rect, String
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.graphics import renderPDF
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: ReportLab not installed. Install with: pip install reportlab")


class OpsPilotPDFGenerator:
    """Professional PDF report generator for OpsPilot++ benchmarks."""
    
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation. Install with: pip install reportlab")
        
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.colors = {
            'primary': colors.Color(0.2, 0.4, 0.8),      # Blue
            'secondary': colors.Color(0.8, 0.4, 0.2),    # Orange
            'success': colors.Color(0.2, 0.8, 0.4),      # Green
            'warning': colors.Color(0.9, 0.7, 0.2),      # Yellow
            'danger': colors.Color(0.8, 0.2, 0.2),       # Red
            'light_gray': colors.Color(0.95, 0.95, 0.95),
            'dark_gray': colors.Color(0.3, 0.3, 0.3)
        }
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the report."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.Color(0.2, 0.4, 0.8)
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.Color(0.3, 0.3, 0.3)
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            spaceBefore=15,
            textColor=colors.Color(0.2, 0.4, 0.8),
            borderWidth=1,
            borderColor=colors.Color(0.2, 0.4, 0.8),
            borderPadding=5
        ))
        
        # Score style (large)
        self.styles.add(ParagraphStyle(
            name='LargeScore',
            parent=self.styles['Normal'],
            fontSize=36,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.Color(0.2, 0.8, 0.4)
        ))
        
        # Metric style
        self.styles.add(ParagraphStyle(
            name='Metric',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=6,
            leftIndent=20
        ))
        
        # Warning style
        self.styles.add(ParagraphStyle(
            name='Warning',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.Color(0.8, 0.2, 0.2),
            backColor=colors.Color(1.0, 0.95, 0.95),
            borderWidth=1,
            borderColor=colors.Color(0.8, 0.2, 0.2),
            borderPadding=8
        ))
    
    def _create_header(self) -> List:
        """Create the report header with title and branding."""
        story = []
        
        # Main title
        title = Paragraph("OpsPilot++ Benchmark Report", self.styles['CustomTitle'])
        story.append(title)
        
        # Subtitle with timestamp
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        subtitle = Paragraph(f"Generated on {timestamp}", self.styles['Subtitle'])
        story.append(subtitle)
        
        # Horizontal line
        story.append(HRFlowable(width="100%", thickness=2, color=self.colors['primary']))
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_executive_summary(self, report_data: Dict[str, Any]) -> List:
        """Create executive summary section."""
        story = []
        
        # Section header
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        # Model name
        model_name = report_data.get('model', 'Unknown Model')
        story.append(Paragraph(f"<b>Model:</b> {model_name}", self.styles['Normal']))
        story.append(Spacer(1, 10))
        
        # Large score display
        score = report_data.get('score', 0.0)
        grade = report_data.get('metadata', {}).get('performance_grade', 'N/A')
        score_text = f"<b>{score:.1%}</b><br/><font size='18'>Grade: {grade}</font>"
        story.append(Paragraph(score_text, self.styles['LargeScore']))
        
        # Overall assessment
        assessment = report_data.get('insights', {}).get('overall_assessment', 'No assessment available')
        story.append(Paragraph(f"<b>Assessment:</b> {assessment}", self.styles['Normal']))
        story.append(Spacer(1, 15))
        
        # Key metrics summary
        regret = report_data.get('regret', 0.0)
        regret_level = report_data.get('insights', {}).get('regret_analysis', {}).get('level', 'Unknown')
        total_failures = report_data.get('metadata', {}).get('total_failures', 0)
        critical_failures = report_data.get('metadata', {}).get('critical_failures', 0)
        
        summary_data = [
            ['Metric', 'Value', 'Status'],
            ['Decision Regret', f'{regret:.1%}', regret_level],
            ['Total Issues', str(total_failures), 'Detected' if total_failures > 0 else 'None'],
            ['Critical Issues', str(critical_failures), 'High Priority' if critical_failures > 0 else 'None']
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_performance_breakdown(self, report_data: Dict[str, Any]) -> List:
        """Create detailed performance breakdown section."""
        story = []
        
        story.append(Paragraph("Performance Breakdown", self.styles['SectionHeader']))
        
        breakdown = report_data.get('breakdown', {})
        if not breakdown:
            story.append(Paragraph("No breakdown data available.", self.styles['Normal']))
            return story
        
        # Create breakdown table
        breakdown_data = [['Category', 'Score', 'Performance']]
        
        for category, score in breakdown.items():
            if isinstance(score, (int, float)):
                # Determine performance level
                if score >= 0.8:
                    performance = "Excellent"
                elif score >= 0.7:
                    performance = "Good"
                elif score >= 0.6:
                    performance = "Satisfactory"
                elif score >= 0.5:
                    performance = "Below Average"
                else:
                    performance = "Poor"
                
                breakdown_data.append([
                    category.replace('_', ' ').title(),
                    f'{score:.1%}',
                    performance
                ])
        
        breakdown_table = Table(breakdown_data, colWidths=[2.5*inch, 1*inch, 1.5*inch])
        breakdown_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), self.colors['light_gray']),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10)
        ]))
        
        story.append(breakdown_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_performance_metrics(self, report_data: Dict[str, Any]) -> List:
        """Create performance metrics section."""
        story = []
        
        story.append(Paragraph("Performance Metrics", self.styles['SectionHeader']))
        
        metrics = report_data.get('performance_metrics', {})
        if not metrics:
            story.append(Paragraph("No performance metrics available.", self.styles['Normal']))
            return story
        
        # Create metrics table
        metrics_data = [['Metric', 'Value', 'Description']]
        
        metric_descriptions = {
            'accuracy': 'Overall correctness of decisions',
            'precision': 'Quality of positive predictions',
            'recall': 'Coverage of actual positives',
            'f1_score': 'Harmonic mean of precision and recall',
            'efficiency': 'Resource utilization effectiveness',
            'consistency': 'Stability across different scenarios'
        }
        
        for metric, value in metrics.items():
            if isinstance(value, (int, float)):
                description = metric_descriptions.get(metric, 'Performance indicator')
                metrics_data.append([
                    metric.replace('_', ' ').title(),
                    f'{value:.1%}',
                    description
                ])
        
        metrics_table = Table(metrics_data, colWidths=[1.5*inch, 1*inch, 2.5*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['secondary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (1, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10)
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_regret_analysis(self, report_data: Dict[str, Any]) -> List:
        """Create regret analysis section."""
        story = []
        
        story.append(Paragraph("Regret Analysis", self.styles['SectionHeader']))
        
        regret = report_data.get('regret', 0.0)
        regret_analysis = report_data.get('insights', {}).get('regret_analysis', {})
        
        # Regret value and level
        regret_level = regret_analysis.get('level', 'Unknown')
        regret_desc = regret_analysis.get('description', 'No description available')
        regret_rec = regret_analysis.get('recommendation', 'No recommendation available')
        
        story.append(Paragraph(f"<b>Regret Score:</b> {regret:.1%} ({regret_level})", self.styles['Normal']))
        story.append(Spacer(1, 10))
        
        story.append(Paragraph(f"<b>Analysis:</b> {regret_desc}", self.styles['Normal']))
        story.append(Spacer(1, 10))
        
        story.append(Paragraph(f"<b>Recommendation:</b> {regret_rec}", self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_failures_section(self, report_data: Dict[str, Any]) -> List:
        """Create failures and issues section."""
        story = []
        
        story.append(Paragraph("Detected Issues and Failures", self.styles['SectionHeader']))
        
        failures = report_data.get('failures', [])
        if not failures:
            story.append(Paragraph("✅ No significant issues detected.", self.styles['Normal']))
            story.append(Spacer(1, 20))
            return story
        
        # Group failures by severity
        critical_failures = []
        high_failures = []
        other_failures = []
        
        for failure in failures:
            severity = failure.get('severity', 'medium') if isinstance(failure, dict) else getattr(failure, 'severity', 'medium')
            if severity == 'critical':
                critical_failures.append(failure)
            elif severity == 'high':
                high_failures.append(failure)
            else:
                other_failures.append(failure)
        
        # Display critical failures first
        if critical_failures:
            story.append(Paragraph("🚨 Critical Issues", self.styles['Heading3']))
            for failure in critical_failures:
                story.extend(self._format_failure(failure, is_critical=True))
        
        # Display high severity failures
        if high_failures:
            story.append(Paragraph("⚠️ High Priority Issues", self.styles['Heading3']))
            for failure in high_failures:
                story.extend(self._format_failure(failure))
        
        # Display other failures
        if other_failures:
            story.append(Paragraph("📋 Other Issues", self.styles['Heading3']))
            for failure in other_failures:
                story.extend(self._format_failure(failure))
        
        story.append(Spacer(1, 20))
        return story
    
    def _format_failure(self, failure: Dict[str, Any], is_critical: bool = False) -> List:
        """Format a single failure for display."""
        story = []
        
        if isinstance(failure, dict):
            failure_type = failure.get('type', 'Unknown')
            description = failure.get('description', 'No description')
            recommendation = failure.get('recommendation', 'No recommendation')
            impact = failure.get('impact', 0.0)
        else:
            failure_type = getattr(failure, 'type', 'Unknown')
            description = getattr(failure, 'description', 'No description')
            recommendation = getattr(failure, 'recommendation', 'No recommendation')
            impact = getattr(failure, 'impact', 0.0)
        
        # Format failure info
        failure_text = f"<b>{failure_type.replace('_', ' ').title()}</b><br/>"
        failure_text += f"Description: {description}<br/>"
        failure_text += f"Impact: {impact:.1%}<br/>"
        failure_text += f"Recommendation: {recommendation}"
        
        if is_critical:
            story.append(Paragraph(failure_text, self.styles['Warning']))
        else:
            story.append(Paragraph(failure_text, self.styles['Normal']))
        
        story.append(Spacer(1, 10))
        return story
    
    def _create_explanation_section(self, report_data: Dict[str, Any]) -> List:
        """Create detailed explanation section."""
        story = []
        
        story.append(Paragraph("Detailed Explanation", self.styles['SectionHeader']))
        
        explanation = report_data.get('explanation', {})
        if not explanation:
            story.append(Paragraph("No detailed explanation available.", self.styles['Normal']))
            return story
        
        # Format explanation data
        for key, value in explanation.items():
            if isinstance(value, str):
                formatted_key = key.replace('_', ' ').title()
                story.append(Paragraph(f"<b>{formatted_key}:</b> {value}", self.styles['Normal']))
                story.append(Spacer(1, 8))
            elif isinstance(value, list):
                formatted_key = key.replace('_', ' ').title()
                story.append(Paragraph(f"<b>{formatted_key}:</b>", self.styles['Normal']))
                for item in value:
                    story.append(Paragraph(f"• {item}", self.styles['Normal']))
                story.append(Spacer(1, 8))
        
        story.append(Spacer(1, 20))
        return story
    
    def _create_recommendations(self, report_data: Dict[str, Any]) -> List:
        """Create recommendations section."""
        story = []
        
        story.append(Paragraph("Recommendations & Next Steps", self.styles['SectionHeader']))
        
        insights = report_data.get('insights', {})
        next_steps = insights.get('next_steps', [])
        strengths = insights.get('strengths', [])
        improvement_areas = insights.get('improvement_areas', [])
        
        # Strengths
        if strengths:
            story.append(Paragraph("✅ <b>Strengths</b>", self.styles['Heading3']))
            for strength in strengths:
                story.append(Paragraph(f"• {strength}", self.styles['Normal']))
            story.append(Spacer(1, 10))
        
        # Improvement areas
        if improvement_areas:
            story.append(Paragraph("🎯 <b>Areas for Improvement</b>", self.styles['Heading3']))
            for area in improvement_areas:
                story.append(Paragraph(f"• {area}", self.styles['Normal']))
            story.append(Spacer(1, 10))
        
        # Next steps
        if next_steps:
            story.append(Paragraph("📋 <b>Recommended Next Steps</b>", self.styles['Heading3']))
            for i, step in enumerate(next_steps, 1):
                story.append(Paragraph(f"{i}. {step}", self.styles['Normal']))
                story.append(Spacer(1, 5))
        
        story.append(Spacer(1, 20))
        return story
    
    def _create_footer(self, report_data: Dict[str, Any]) -> List:
        """Create report footer with metadata."""
        story = []
        
        # Horizontal line
        story.append(HRFlowable(width="100%", thickness=1, color=self.colors['dark_gray']))
        story.append(Spacer(1, 10))
        
        # Metadata
        metadata = report_data.get('metadata', {})
        timestamp = report_data.get('timestamp', datetime.now().isoformat())
        
        footer_text = f"Report generated by {metadata.get('generator', 'OpsPilot++ Report Generator')} "
        footer_text += f"v{metadata.get('report_version', '1.0.0')} on {timestamp}"
        
        story.append(Paragraph(footer_text, self.styles['Normal']))
        
        return story


def create_pdf(report_data: Dict[str, Any], filename: str) -> bool:
    """
    Create a professional PDF report from OpsPilot++ benchmark data.
    
    Args:
        report_data: Dictionary containing report data with keys:
            - model: Model name
            - score: Performance score (0-1)
            - breakdown: Score breakdown dictionary
            - regret: Regret value
            - failures: List of failure objects/dicts
            - explanation: Explanation dictionary
            - performance_metrics: Performance metrics
            - insights: Analysis insights
            - metadata: Report metadata
        filename: Output filename (without .pdf extension)
    
    Returns:
        bool: True if PDF was created successfully, False otherwise
    """
    if not REPORTLAB_AVAILABLE:
        print("Error: ReportLab is not installed. Install with: pip install reportlab")
        return False
    
    try:
        # Ensure output directory exists
        output_dir = Path("/mnt/data")
        if not output_dir.exists():
            # Fallback to current directory if /mnt/data doesn't exist
            output_dir = Path(".")
        
        output_path = output_dir / f"{filename}.pdf"
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Initialize PDF generator
        generator = OpsPilotPDFGenerator()
        
        # Build story (content)
        story = []
        
        # Add sections
        story.extend(generator._create_header())
        story.extend(generator._create_executive_summary(report_data))
        story.extend(generator._create_performance_breakdown(report_data))
        story.extend(generator._create_performance_metrics(report_data))
        story.extend(generator._create_regret_analysis(report_data))
        story.extend(generator._create_failures_section(report_data))
        story.extend(generator._create_explanation_section(report_data))
        story.extend(generator._create_recommendations(report_data))
        story.extend(generator._create_footer(report_data))
        
        # Build PDF
        doc.build(story)
        
        print(f"✅ PDF report created successfully: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating PDF report: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_pdf_from_json(json_file: str, output_filename: str) -> bool:
    """
    Create PDF report from JSON file.
    
    Args:
        json_file: Path to JSON report file
        output_filename: Output PDF filename (without extension)
    
    Returns:
        bool: Success status
    """
    try:
        import json
        
        with open(json_file, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        return create_pdf(report_data, output_filename)
        
    except Exception as e:
        print(f"❌ Error reading JSON file: {e}")
        return False


# Utility function for batch PDF generation
def create_multiple_pdfs(reports: List[Dict[str, Any]], base_filename: str) -> List[str]:
    """
    Create multiple PDF reports from a list of report data.
    
    Args:
        reports: List of report data dictionaries
        base_filename: Base filename for PDFs
    
    Returns:
        List of created PDF filenames
    """
    created_files = []
    
    for i, report_data in enumerate(reports):
        filename = f"{base_filename}_{i+1}"
        if create_pdf(report_data, filename):
            created_files.append(f"{filename}.pdf")
    
    return created_files


if __name__ == "__main__":
    # Example usage
    sample_report = {
        "model": "GPT-4 Test Agent",
        "score": 0.85,
        "breakdown": {
            "email_handling": 0.9,
            "task_prioritization": 0.8,
            "time_management": 0.75,
            "customer_satisfaction": 0.95,
            "resource_efficiency": 0.7
        },
        "regret": 0.15,
        "failures": [
            {
                "type": "time_management",
                "severity": "medium",
                "description": "Occasional delays in task completion",
                "impact": 0.6,
                "recommendation": "Implement better scheduling algorithms"
            }
        ],
        "explanation": {
            "strengths": "Excellent customer service and email handling",
            "weaknesses": "Room for improvement in resource efficiency",
            "recommendations": "Focus on optimizing resource allocation"
        },
        "performance_metrics": {
            "accuracy": 0.85,
            "precision": 0.88,
            "recall": 0.82,
            "f1_score": 0.85,
            "efficiency": 0.78,
            "consistency": 0.90
        },
        "insights": {
            "overall_assessment": "Good performance with room for optimization",
            "regret_analysis": {
                "level": "Moderate",
                "description": "Some suboptimal decisions detected",
                "recommendation": "Review decision criteria"
            },
            "strengths": ["Excellent customer service", "High consistency"],
            "improvement_areas": ["Resource optimization", "Time management"],
            "next_steps": [
                "Implement resource optimization algorithms",
                "Enhance time management protocols",
                "Conduct performance review"
            ]
        },
        "metadata": {
            "report_version": "1.0.0",
            "generator": "OpsPilot++ Report Generator",
            "total_failures": 1,
            "critical_failures": 0,
            "performance_grade": "A-"
        },
        "timestamp": datetime.now().isoformat()
    }
    
    # Create sample PDF
    success = create_pdf(sample_report, "sample_opspilot_report")
    if success:
        print("Sample PDF created successfully!")
    else:
        print("Failed to create sample PDF.")