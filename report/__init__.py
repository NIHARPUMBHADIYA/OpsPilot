"""
OpsPilot++ Report Generation Module

This module provides comprehensive reporting capabilities for AI agent performance,
including score analysis, failure mode detection, detailed explanations, and PDF generation.
"""

from .generator import generate_report, ReportGenerator

# Try to import PDF functionality
try:
    from .pdf import create_pdf, create_pdf_from_json, create_multiple_pdfs, REPORTLAB_AVAILABLE
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: PDF generation not available. Install reportlab: pip install reportlab")
    
    # Create dummy functions
    def create_pdf(*args, **kwargs):
        raise ImportError("ReportLab not installed. Install with: pip install reportlab")
    
    def create_pdf_from_json(*args, **kwargs):
        raise ImportError("ReportLab not installed. Install with: pip install reportlab")
    
    def create_multiple_pdfs(*args, **kwargs):
        raise ImportError("ReportLab not installed. Install with: pip install reportlab")

__all__ = ['generate_report', 'ReportGenerator', 'create_pdf', 'create_pdf_from_json', 'create_multiple_pdfs', 'REPORTLAB_AVAILABLE']