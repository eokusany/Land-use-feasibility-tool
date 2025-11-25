from flask import Flask, render_template, request, jsonify, send_file
import os
import json
from datetime import datetime
from property_parser import PropertyParser
from municipality_lookup import MunicipalityLookup
from policy_retrieval import PolicyRetrieval
from report_generator import ReportGenerator

app = Flask(__name__)

# Initialize components
property_parser = PropertyParser()
municipality_lookup = MunicipalityLookup()
policy_retrieval = PolicyRetrieval()
report_generator = ReportGenerator()

@app.route('/')
def index():
    """Main page for the Alberta Land Use Feasibility Tool"""
    return render_template('index.html')

@app.route('/api/analyze_property', methods=['POST'])
def analyze_property():
    """Analyze property and return land use information"""
    try:
        data = request.get_json()
        
        # Parse property information
        property_info = property_parser.parse_property_info(
            address=data.get('address', ''),
            legal_description=data.get('legal_description', ''),
            additional_info=data.get('additional_info', '')
        )
        
        if not property_info:
            return jsonify({'error': 'Unable to parse property information'}), 400
        
        # Lookup municipality
        municipality_info = municipality_lookup.find_municipality(property_info)
        
        if not municipality_info:
            return jsonify({'error': 'Municipality not found or not supported'}), 404
        
        # Retrieve policies and zoning information
        policy_info = policy_retrieval.get_land_use_policies(
            municipality_info, property_info
        )
        
        # Compile results
        results = {
            'property_info': property_info,
            'municipality_info': municipality_info,
            'policy_info': policy_info,
            'analysis_date': datetime.now().isoformat(),
            'feasibility_summary': _generate_feasibility_summary(policy_info)
        }
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_report', methods=['POST'])
def generate_report():
    """Generate a PDF report for the property analysis"""
    try:
        data = request.get_json()
        
        # Generate PDF report
        report_path = report_generator.create_report(data)
        
        return send_file(
            report_path,
            as_attachment=True,
            download_name=f"land_use_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/municipalities')
def get_municipalities():
    """Get list of supported municipalities"""
    municipalities = municipality_lookup.get_supported_municipalities()
    return jsonify(municipalities)

def _generate_feasibility_summary(policy_info):
    """Generate a feasibility summary based on policy information"""
    summary = {
        'development_potential': 'Unknown',
        'key_considerations': [],
        'recommended_actions': []
    }
    
    if policy_info.get('zoning'):
        zoning = policy_info['zoning']
        
        # Analyze zoning for development potential
        if any(term in zoning.lower() for term in ['residential', 'commercial', 'mixed']):
            summary['development_potential'] = 'High'
        elif any(term in zoning.lower() for term in ['agricultural', 'rural']):
            summary['development_potential'] = 'Moderate'
        else:
            summary['development_potential'] = 'Low'
    
    # Add key considerations
    if policy_info.get('setbacks'):
        summary['key_considerations'].append(f"Setback requirements: {policy_info['setbacks']}")
    
    if policy_info.get('density_restrictions'):
        summary['key_considerations'].append(f"Density restrictions: {policy_info['density_restrictions']}")
    
    if policy_info.get('special_provisions'):
        summary['key_considerations'].extend(policy_info['special_provisions'])
    
    # Add recommended actions
    summary['recommended_actions'] = [
        'Consult with municipal planning department',
        'Review detailed zoning bylaws',
        'Consider environmental assessments if required',
        'Verify utility availability and capacity'
    ]
    
    return summary

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=False)
