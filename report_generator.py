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
        
        province = data.get("municipality_info", {}).get("province_name", "")
        report_info = [
            f"Report Date: {formatted_date}",
            f"Prepared by: Plotline — Canadian Land Use Feasibility Platform",
            f"Province / Territory: {province}" if province else "Province / Territory: Not specified",
            "Report Type: Preliminary Feasibility Assessment",
        ]
        
        for info in report_info:
            story.append(Paragraph(info, self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        story.append(Spacer(1, 1*inch))
        
        # Disclaimer
        disclaimer = """
        <b>DISCLAIMER:</b> This report is generated by Plotline and is based on publicly available
        information and automated analysis covering municipalities across Canada. It is intended for
        preliminary assessment purposes only. All information must be verified with the appropriate
        municipal and provincial authorities before making any development decisions. This report
        does not constitute professional planning, engineering, or legal advice.
        """
        story.append(Paragraph(disclaimer, self.styles['Highlight']))
        
        return story
    
    def _create_executive_summary(self, data: Dict) -> List:
        """Create executive summary section"""
        story = []

        story.append(Paragraph("Executive Summary", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.3*inch))

        policy_info = data.get('policy_info', {}) or {}
        is_verified = policy_info.get('verification_status') == 'verified'

        # Banner — different copy for verified vs unverified
        if is_verified:
            zone_str = policy_info.get('zoning') or 'Unknown zone'
            source = policy_info.get('zone_source') or 'the municipality'
            banner = (
                f"<b>ZONE VERIFIED.</b> The base zone for this parcel was retrieved from "
                f"{source}: <b>{zone_str}</b>. Setbacks, height limits, density, and permitted "
                "uses are not extracted by Plotline and must be read from the linked bylaw section. "
                "Site-specific amendments and discretionary variances are not in the open dataset — "
                "confirm with the municipal planning department before making development decisions."
            )
        else:
            banner = (
                "<b>VERIFICATION REQUIRED.</b> This report identifies the municipality and provides "
                "general planning references only. Plotline does <b>not</b> retrieve parcel-level "
                "zoning data for this municipality. The specific zone designation, permitted uses, "
                "setbacks, height limits, and density restrictions for this property must be "
                "confirmed directly with the municipal planning department before any development "
                "decision is made."
            )
        story.append(Paragraph(banner, self.styles['Highlight']))
        story.append(Spacer(1, 0.2*inch))

        # Summary table — adapts to verified status
        if is_verified:
            zoning_row = policy_info.get('zoning') or 'Verified — see Zoning Reference section'
            status_label = 'Zone Verified — Bylaw Review Required'
        else:
            zoning_row = 'Not retrieved — must be verified with municipality'
            status_label = 'Preliminary — Verification Required'

        summary_data = [
            ['Assessment Category', 'Result'],
            ['Status', status_label],
            ['Municipality', data.get('municipality_info', {}).get('name', 'Not Identified')],
            ['Province / Territory', data.get('municipality_info', {}).get('province_name', 'Not specified')],
            ['Parcel-Level Zoning', zoning_row],
            ['Report Date', datetime.now().strftime('%B %d, %Y')]
        ]

        summary_table = Table(summary_data, colWidths=[2.5*inch, 3.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))

        # Key considerations from the (now honest) feasibility summary
        feasibility_summary = data.get('feasibility_summary', {})
        story.append(Paragraph("Key Considerations", self.styles['SectionHeader']))
        for consideration in feasibility_summary.get('key_considerations', []):
            story.append(Paragraph(f"• {consideration}", self.styles['Normal']))

        story.append(Spacer(1, 0.2*inch))

        # Top recommended actions
        story.append(Paragraph("Immediate Recommended Actions", self.styles['SectionHeader']))
        for i, action in enumerate(feasibility_summary.get('recommended_actions', [])[:3], 1):
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
            ['Address', raw_input.get('address', 'Not provided') or 'Not provided'],
        ]
        if raw_input.get('legal_description'):
            property_details.append(['Legal Description', raw_input['legal_description']])
        
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
        """Create zoning and policy reference section.

        We do not have parcel-level zoning, so this section now points the
        user at the authoritative sources (bylaw URL, planning department)
        and lists the verification steps and generic dev requirements.
        """
        story = []

        story.append(Paragraph("Zoning and Policy Reference", self.styles['Subtitle']))
        story.append(Spacer(1, 0.2*inch))

        policy_info = data.get('policy_info', {})
        municipality_info = data.get('municipality_info', {})

        if not policy_info:
            story.append(Paragraph("Policy information not available.", self.styles['Normal']))
            return story

        is_verified = policy_info.get('verification_status') == 'verified'

        if is_verified:
            # --- Verified zone block ---
            story.append(Paragraph("Parcel Zone (Verified)", self.styles['SectionHeader']))

            zone_table_rows = [
                ['Zone Code', policy_info.get('zoning_code') or '—'],
                ['Zone Name', (policy_info.get('zoning') or '').split(' — ', 1)[-1] or '—'],
                ['Source', policy_info.get('zone_source') or '—'],
                ['Retrieved', policy_info.get('zone_retrieved_at') or '—'],
            ]
            zone_table = Table(zone_table_rows, colWidths=[1.6*inch, 4.4*inch])
            zone_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(zone_table)
            story.append(Spacer(1, 0.1*inch))

            # Bylaw section deep link (per zone)
            section_url = policy_info.get('zone_bylaw_section_url')
            if section_url:
                story.append(Paragraph(
                    f'<b>Bylaw section for this zone:</b> '
                    f'<a href="{section_url}" color="blue">{section_url}</a>',
                    self.styles['Normal'],
                ))
                story.append(Paragraph(
                    "<i>This is the authoritative source for setbacks, height limits, density, "
                    "and permitted uses for this zone. Plotline does not parse bylaw text — "
                    "read the linked section for the actual rules.</i>",
                    self.styles['Normal'],
                ))
                story.append(Spacer(1, 0.1*inch))

            # Provider notes (e.g. for DC1/DC2 site-specific zones)
            for note in policy_info.get('zone_provider_notes') or []:
                story.append(Paragraph(f"<b>Note:</b> {note}", self.styles['Highlight']))
                story.append(Spacer(1, 0.05*inch))

            # Overlays
            overlays = policy_info.get('zone_overlays') or []
            if overlays:
                story.append(Paragraph("Overlay Zones in Effect", self.styles['SectionHeader']))
                story.append(Paragraph(
                    "<i>Overlay zones add or modify rules on top of the base zone above.</i>",
                    self.styles['Normal'],
                ))
                for o in overlays:
                    bylaw_no = f" (Bylaw {o['bylaw_no']})" if o.get('bylaw_no') else ""
                    story.append(Paragraph(
                        f"• <b>{o['code']}</b> — {o['description']}{bylaw_no}",
                        self.styles['Normal'],
                    ))
                story.append(Spacer(1, 0.1*inch))

            # Caveat — even verified zones still need municipal confirmation
            story.append(Paragraph(
                "<b>Important:</b> Site-specific amendments, previously granted variances, and "
                "Direct Control conditions are not in the open dataset. Confirm the parcel-level "
                "rules with the municipal planning department before making development decisions.",
                self.styles['Highlight'],
            ))
            story.append(Spacer(1, 0.1*inch))

        else:
            # --- Unverified status callout (Option A copy) ---
            story.append(Paragraph("Parcel-Level Zoning", self.styles['SectionHeader']))
            zoning_status = policy_info.get(
                'zoning_status',
                'Not retrieved. Parcel-level zoning must be verified directly with the municipal planning department.'
            )
            story.append(Paragraph(f"<b>Status:</b> {zoning_status}", self.styles['Highlight']))

            # Surface provider failure messages so the user knows what happened
            verification_message = policy_info.get('verification_message')
            if verification_message:
                story.append(Paragraph(f"<i>{verification_message}</i>", self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))

        # Land use bylaw link (always shown when known)
        bylaw = policy_info.get('land_use_bylaw') or {}
        if bylaw.get('url'):
            story.append(Paragraph("Land Use Bylaw", self.styles['SectionHeader']))
            story.append(Paragraph(
                f"<b>{bylaw.get('title', 'Land Use Bylaw')}:</b> "
                f'<a href="{bylaw["url"]}" color="blue">{bylaw["url"]}</a>',
                self.styles['Normal'],
            ))
            if not is_verified:
                story.append(Paragraph(
                    "Use the municipality's online zoning map (linked from the bylaw page above) "
                    "to look up the current zone designation for this parcel.",
                    self.styles['Normal'],
                ))
            story.append(Spacer(1, 0.1*inch))

        # Verification steps
        verification_steps = policy_info.get('verification_steps', [])
        if verification_steps:
            story.append(Paragraph("How to Verify Zoning for This Property", self.styles['SectionHeader']))
            for i, step in enumerate(verification_steps, 1):
                story.append(Paragraph(f"{i}. {step}", self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))

        # Generic development requirements (province-aware, not parcel-specific)
        dev_requirements = policy_info.get('development_requirements', [])
        if dev_requirements:
            story.append(Paragraph("General Development Requirements", self.styles['SectionHeader']))
            story.append(Paragraph(
                "<i>The following apply to most development in this jurisdiction. "
                "Site-specific requirements must still be confirmed with the municipality.</i>",
                self.styles['Normal'],
            ))
            for requirement in dev_requirements:
                story.append(Paragraph(f"• {requirement}", self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))

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
        
        province = data.get("municipality_info", {}).get("province", "")
        planning_act = data.get("municipality_info", {}).get("planning_act", "")
        building_code = data.get("municipality_info", {}).get("building_code", "National Building Code of Canada")
        references = [
            "Canada Lands Survey System (clss.nrcan.gc.ca)",
            "National Building Code of Canada",
            building_code,
            planning_act if planning_act else "Municipal / Provincial Planning Act",
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
        This preliminary report was generated by Plotline — Canadian Land Use Feasibility Platform.
        Plotline performs property identification (address parsing and geocoding), municipality
        lookup against a database of Canadian municipalities, and provides links to the relevant
        municipal land use bylaw and provincial planning legislation.

        <b>Plotline does NOT retrieve parcel-level zoning data.</b> The specific zone designation,
        permitted uses, setbacks, height limits, density restrictions, and any site-specific
        overlays for a given property are not determined by this tool and must be verified
        directly with the municipal planning department before any development decision is made.

        This report is intended as a starting point for due diligence — not as a substitute for
        professional planning, engineering, or legal advice.
        """
        
        story.append(Paragraph(methodology_text, self.styles['Normal']))
        
        return story
