from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import os
from datetime import datetime
from typing import Dict, List

class ReportGenerator:
    """Generate PDF reports for land use feasibility studies"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
        # Create reports directory if it doesn't exist
        self.reports_dir = "reports"
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue,
            borderWidth=1,
            borderColor=colors.darkblue,
            borderPadding=5
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=6,
            spaceBefore=12,
            textColor=colors.darkgreen
        ))
        
        # Highlight style
        self.styles.add(ParagraphStyle(
            name='Highlight',
            parent=self.styles['Normal'],
            backColor=colors.lightgrey,
            borderWidth=1,
            borderColor=colors.grey,
            borderPadding=8,
            spaceAfter=12
        ))
    
    def create_report(self, analysis_data: Dict) -> str:
        """
        Create a comprehensive PDF report
        
        Args:
            analysis_data: Complete analysis data from the API
            
        Returns:
            Path to the generated PDF report
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"land_use_feasibility_report_{timestamp}.pdf"
        filepath = os.path.join(self.reports_dir, filename)
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build the story (content)
        story = []
        
        # Title page
        story.extend(self._create_title_page(analysis_data))
        story.append(PageBreak())
        
        # Executive summary
        story.extend(self._create_executive_summary(analysis_data))
        story.append(PageBreak())
        
        # Property information
        story.extend(self._create_property_section(analysis_data))
        
        # Municipality information
        story.extend(self._create_municipality_section(analysis_data))
        
        # Zoning and policy analysis
        story.extend(self._create_policy_section(analysis_data))
        
        # Development analysis (if cottage development data available)
        if 'cottage_analysis' in analysis_data:
            story.extend(self._create_development_analysis(analysis_data))
        
        # Recommendations and next steps
        story.extend(self._create_recommendations_section(analysis_data))
        
        # Appendices
        story.append(PageBreak())
        story.extend(self._create_appendices(analysis_data))
        
        # Build the PDF
        doc.build(story)
        
        return filepath
    
    def _create_title_page(self, data: Dict) -> List:
        """Create the title page"""
        story = []
        
        # Main title
        story.append(Paragraph("Land Use Feasibility Study", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5*inch))
        
        # Property identifier
        property_info = data.get('property_info', {})
        address = property_info.get('raw_input', {}).get('address', 'Property Address Not Available')
        
        story.append(Paragraph(f"Property: {address}", self.styles['Subtitle']))
        story.append(Spacer(1, 0.3*inch))
        
        # Municipality
        municipality_info = data.get('municipality_info', {})
        municipality_name = municipality_info.get('name', 'Municipality Not Identified')
        
        story.append(Paragraph(f"Municipality: {municipality_name}", self.styles['Heading2']))
        story.append(Spacer(1, 0.5*inch))
        
        # Report details
        analysis_date = data.get('analysis_date', datetime.now().isoformat())
        formatted_date = datetime.fromisoformat(analysis_date.replace('Z', '+00:00')).strftime('%B %d, %Y')
        
        report_info = [
            f"Report Date: {formatted_date}",
            "Prepared by: Alberta Land Use Feasibility Tool",
            "Report Type: Preliminary Feasibility Assessment"
        ]
        
        for info in report_info:
            story.append(Paragraph(info, self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        story.append(Spacer(1, 1*inch))
        
        # Disclaimer
        disclaimer = """
        <b>DISCLAIMER:</b> This report is based on publicly available information and automated analysis. 
        It is intended for preliminary assessment purposes only. All information should be verified with 
        the appropriate municipal authorities before making any development decisions. This report does 
        not constitute professional planning or legal advice.
        """
        story.append(Paragraph(disclaimer, self.styles['Highlight']))
        
        return story
    
    def _create_executive_summary(self, data: Dict) -> List:
        """Create executive summary section"""
        story = []
        
        story.append(Paragraph("Executive Summary", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.3*inch))
        
        # Feasibility summary
        feasibility_summary = data.get('feasibility_summary', {})
        development_potential = feasibility_summary.get('development_potential', 'Unknown')
        
        # Create summary table
        summary_data = [
            ['Assessment Category', 'Result'],
            ['Development Potential', development_potential],
            ['Municipality', data.get('municipality_info', {}).get('name', 'Not Identified')],
            ['Primary Zoning', data.get('policy_info', {}).get('zoning', 'Not Determined')],
            ['Report Date', datetime.now().strftime('%B %d, %Y')]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Key findings
        story.append(Paragraph("Key Findings", self.styles['SectionHeader']))
        
        key_considerations = feasibility_summary.get('key_considerations', [])
        if key_considerations:
            for consideration in key_considerations[:5]:  # Limit to top 5
                story.append(Paragraph(f"• {consideration}", self.styles['Normal']))
        else:
            story.append(Paragraph("• Detailed analysis required to determine key considerations", self.styles['Normal']))
        
        story.append(Spacer(1, 0.2*inch))
        
        # Recommended actions
        story.append(Paragraph("Immediate Recommended Actions", self.styles['SectionHeader']))
        
        recommended_actions = feasibility_summary.get('recommended_actions', [])
        if recommended_actions:
            for i, action in enumerate(recommended_actions[:3], 1):  # Top 3 actions
                story.append(Paragraph(f"{i}. {action}", self.styles['Normal']))
        
        return story
    
    def _create_property_section(self, data: Dict) -> List:
        """Create property information section"""
        story = []
        
        story.append(Paragraph("Property Information", self.styles['Subtitle']))
        story.append(Spacer(1, 0.2*inch))
        
        property_info = data.get('property_info', {})
        raw_input = property_info.get('raw_input', {})
        
        # Basic property details
        story.append(Paragraph("Property Details", self.styles['SectionHeader']))
        
        property_details = [
            ['Address', raw_input.get('address', 'Not provided')],
            ['Legal Description', raw_input.get('legal_description', 'Not provided')],
        ]
        
        # Add coordinates if available
        coordinates = property_info.get('coordinates')
        if coordinates:
            lat_lon = f"{coordinates.get('latitude', 'N/A'):.6f}, {coordinates.get('longitude', 'N/A'):.6f}"
            property_details.append(['Coordinates', lat_lon])
        
        # Add property characteristics
        property_chars = property_info.get('property_details', {})
        if property_chars.get('acreage'):
            property_details.append(['Acreage', f"{property_chars['acreage']} acres"])
        
        property_table = Table(property_details, colWidths=[2*inch, 4*inch])
        property_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(property_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Additional information if provided
        additional_info = raw_input.get('additional_info', '')
        if additional_info:
            story.append(Paragraph("Additional Property Information", self.styles['SectionHeader']))
            story.append(Paragraph(additional_info, self.styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
        
        return story
    
    def _create_municipality_section(self, data: Dict) -> List:
        """Create municipality information section"""
        story = []
        
        story.append(Paragraph("Municipality Information", self.styles['Subtitle']))
        story.append(Spacer(1, 0.2*inch))
        
        municipality_info = data.get('municipality_info', {})
        
        if not municipality_info:
            story.append(Paragraph("Municipality information not available.", self.styles['Normal']))
            return story
        
        # Basic municipality details
        muni_details = [
            ['Municipality', municipality_info.get('name', 'Not identified')],
            ['Type', municipality_info.get('type', 'Not specified')],
            ['Website', municipality_info.get('website', 'Not available')],
        ]
        
        # Add population if available
        if municipality_info.get('population'):
            muni_details.append(['Population', f"{municipality_info['population']:,}"])
        
        muni_table = Table(muni_details, colWidths=[2*inch, 4*inch])
        muni_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(muni_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Contact information
        contact_info = municipality_info.get('contact_info', {})
        if contact_info:
            story.append(Paragraph("Municipal Contact Information", self.styles['SectionHeader']))
            
            contact_details = []
            if contact_info.get('phone'):
                contact_details.append(['Phone', contact_info['phone']])
            if contact_info.get('address'):
                contact_details.append(['Address', contact_info['address']])
            if municipality_info.get('planning_dept'):
                contact_details.append(['Planning Department', municipality_info['planning_dept']])
            
            if contact_details:
                contact_table = Table(contact_details, colWidths=[2*inch, 4*inch])
                contact_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(contact_table)
        
        return story
    
    def _create_policy_section(self, data: Dict) -> List:
        """Create zoning and policy analysis section"""
        story = []
        
        story.append(Paragraph("Zoning and Policy Analysis", self.styles['Subtitle']))
        story.append(Spacer(1, 0.2*inch))
        
        policy_info = data.get('policy_info', {})
        
        if not policy_info:
            story.append(Paragraph("Policy information not available.", self.styles['Normal']))
            return story
        
        # Zoning information
        zoning = policy_info.get('zoning')
        if zoning:
            story.append(Paragraph("Current Zoning", self.styles['SectionHeader']))
            story.append(Paragraph(f"<b>Zoning Classification:</b> {zoning}", self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        # Permitted uses
        permitted_uses = policy_info.get('permitted_uses', [])
        if permitted_uses:
            story.append(Paragraph("Permitted Uses", self.styles['SectionHeader']))
            for use in permitted_uses:
                story.append(Paragraph(f"• {use}", self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        # Discretionary uses
        discretionary_uses = policy_info.get('discretionary_uses', [])
        if discretionary_uses:
            story.append(Paragraph("Discretionary Uses", self.styles['SectionHeader']))
            for use in discretionary_uses:
                story.append(Paragraph(f"• {use}", self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        # Development requirements
        dev_requirements = policy_info.get('development_requirements', [])
        if dev_requirements:
            story.append(Paragraph("Development Requirements", self.styles['SectionHeader']))
            for requirement in dev_requirements:
                story.append(Paragraph(f"• {requirement}", self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        # Setbacks and restrictions
        setbacks = policy_info.get('setbacks', {})
        density = policy_info.get('density_restrictions', {})
        height = policy_info.get('height_restrictions', {})
        
        if setbacks or density or height:
            story.append(Paragraph("Development Standards", self.styles['SectionHeader']))
            
            standards_data = [['Standard', 'Requirement']]
            
            for key, value in setbacks.items():
                standards_data.append([f"{key.title()} Setback", value])
            
            for key, value in density.items():
                standards_data.append([key.replace('_', ' ').title(), value])
            
            for key, value in height.items():
                standards_data.append([key.replace('_', ' ').title(), value])
            
            if len(standards_data) > 1:
                standards_table = Table(standards_data, colWidths=[3*inch, 3*inch])
                standards_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(standards_table)
        
        return story
    
    def _create_development_analysis(self, data: Dict) -> List:
        """Create development analysis section"""
        story = []
        
        story.append(Paragraph("Development Analysis", self.styles['Subtitle']))
        story.append(Spacer(1, 0.2*inch))
        
        cottage_analysis = data.get('cottage_analysis', {})
        
        # Development feasibility
        feasibility = cottage_analysis.get('feasibility', 'Unknown')
        story.append(Paragraph(f"<b>Development Feasibility:</b> {feasibility}", self.styles['Highlight']))
        story.append(Spacer(1, 0.2*inch))
        
        # Cottage potential
        cottage_potential = cottage_analysis.get('cottage_potential', {})
        if cottage_potential:
            story.append(Paragraph("Cottage Development Potential", self.styles['SectionHeader']))
            
            potential_data = []
            for key, value in cottage_potential.items():
                formatted_key = key.replace('_', ' ').title()
                potential_data.append([formatted_key, str(value)])
            
            if potential_data:
                potential_table = Table(potential_data, colWidths=[3*inch, 3*inch])
                potential_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(potential_table)
        
        return story
    
    def _create_recommendations_section(self, data: Dict) -> List:
        """Create recommendations and next steps section"""
        story = []
        
        story.append(Paragraph("Recommendations and Next Steps", self.styles['Subtitle']))
        story.append(Spacer(1, 0.2*inch))
        
        feasibility_summary = data.get('feasibility_summary', {})
        recommended_actions = feasibility_summary.get('recommended_actions', [])
        
        if recommended_actions:
            story.append(Paragraph("Recommended Actions", self.styles['SectionHeader']))
            for i, action in enumerate(recommended_actions, 1):
                story.append(Paragraph(f"{i}. {action}", self.styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
        
        # Additional recommendations
        story.append(Paragraph("Additional Considerations", self.styles['SectionHeader']))
        additional_recommendations = [
            "Engage a qualified land use planner for detailed analysis",
            "Conduct environmental due diligence assessments",
            "Verify all utility capacities and connection costs",
            "Review neighboring property developments and restrictions",
            "Consider market analysis for proposed development type",
            "Evaluate financing options and development timeline"
        ]
        
        for recommendation in additional_recommendations:
            story.append(Paragraph(f"• {recommendation}", self.styles['Normal']))
        
        return story
    
    def _create_appendices(self, data: Dict) -> List:
        """Create appendices section"""
        story = []
        
        story.append(Paragraph("Appendices", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.3*inch))
        
        # Appendix A: Data sources
        story.append(Paragraph("Appendix A: Data Sources and References", self.styles['SectionHeader']))
        
        municipality_info = data.get('municipality_info', {})
        
        references = [
            "Alberta Land-use Framework (landuse.alberta.ca)",
            "Municipal Government Act (MGA)",
            "Alberta Building Code"
        ]
        
        if municipality_info.get('website'):
            references.append(f"Municipality Website: {municipality_info['website']}")
        
        if municipality_info.get('land_use_bylaw'):
            references.append(f"Land Use Bylaw: {municipality_info['land_use_bylaw']}")
        
        for reference in references:
            story.append(Paragraph(f"• {reference}", self.styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Appendix B: Methodology
        story.append(Paragraph("Appendix B: Analysis Methodology", self.styles['SectionHeader']))
        
        methodology_text = """
        This feasibility study was conducted using the Alberta Land Use Feasibility Tool, which employs 
        automated analysis of publicly available municipal data, zoning information, and land use policies. 
        The analysis includes property identification, municipality lookup, zoning classification, and 
        policy interpretation based on standard Alberta municipal planning practices.
        
        The tool provides preliminary assessments based on available data and should be supplemented 
        with professional planning consultation and municipal verification for final development decisions.
        """
        
        story.append(Paragraph(methodology_text, self.styles['Normal']))
        
        return story
