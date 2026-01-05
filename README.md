# 🏡 Alberta Land Use Feasibility Tool

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A comprehensive web application for analyzing land use policies and development potential for properties in Central and Northern Alberta. This tool helps developers, planners, and property investors quickly assess feasibility by automatically retrieving municipal zoning information, land use policies, and generating professional feasibility reports.

##  Perfect For
- **Land Developers** - Quickly assess development potential
- **Property Investors** - Evaluate investment opportunities  
- **Planning Consultants** - Streamline feasibility studies
- **Real Estate Professionals** - Provide detailed property analysis

## Quick Demo
![Tool Demo](https://via.placeholder.com/800x400/2c5aa0/ffffff?text=Alberta+Land+Use+Tool+Demo)

*Transform property emails into professional feasibility reports in minutes!*

## Features

### Core Functionality
- **Property Analysis**: Parse addresses and legal descriptions to identify properties
- **Municipality Lookup**: Automatically identify relevant municipalities and jurisdictions
- **Zoning Information**: Retrieve current zoning, permitted uses, and development requirements
- **Policy Retrieval**: Access municipal land use bylaws and statutory plans
- **Feasibility Assessment**: Automated analysis of development potential
- **Professional Reports**: Generate comprehensive PDF feasibility reports

### Supported Regions
Currently supports municipalities between Red Deer and Athabasca, including:

**Cities & Towns:**
- Red Deer, Edmonton, Lacombe, Wetaskiwin, Camrose, Athabasca

**Counties:**
- Lacombe County, Ponoka County, Wetaskiwin County, Camrose County
- Leduc County, Strathcona County, Sturgeon County, Parkland County, Athabasca County

## Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Git (for cloning)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/eokusany/Land-use-feasibility-tool.git
cd Land-use-feasibility-tool
```

2. **Run the setup script (recommended):**
```bash
chmod +x setup.sh
./setup.sh
```

**Or install manually:**

3. **Create a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

5. **Run the application:**
```bash
python app.py
```

6. **Access the tool:**
Open your web browser and navigate to `http://localhost:5001`

### Test Installation
```bash
python test_sample_property.py
```

## 📋 Usage

### Basic Property Analysis

1. **Enter Property Information:**
   - **Address**: Street address or rural address (e.g., "123 Main St, Red Deer, AB" or "RR 1, Lacombe County")
   - **Legal Description**: Legal land description (e.g., "NE 12-45-26-W4M" or "Lot 1, Block 2, Plan 123456")
   - **Additional Info**: Paste email content or provide development details, acreage, etc.

2. **Click "Analyze Property"** to retrieve:
   - Municipality identification
   - Current zoning classification
   - Permitted and discretionary uses
   - Development requirements and restrictions
   - Setback and density requirements
   - Municipal contact information

3. **Generate PDF Report** for professional documentation

### Example Use Case: Cottage Development

Based on your sample email about the 14.55-acre rural commercial property near Pigeon Lake:

**Input:**
- Address: "Property north of Black Bull Golf, west of The Village at Pigeon Lake"
- Legal Description: [Your legal description]
- Additional Info: "14.55 acre rural commercial property. Plan to develop north section with small cottages for rent, 600-800sq ft per unit, 4-5 cottages per acre. County installed septic lift station to north. No village water - drill wells. Highway has turning lanes to county road access."

**Expected Output:**
- Municipality: Wetaskiwin County (or relevant jurisdiction)
- Zoning: Rural Commercial (RC)
- Cottage development feasibility assessment
- Density calculations (potential for 50+ cottage units)
- Infrastructure considerations (septic, water, access)
- Regulatory requirements and next steps

## System Architecture

### Core Components

1. **Property Parser** (`property_parser.py`)
   - Parses addresses and legal descriptions
   - Geocoding for coordinate identification
   - Extracts property characteristics from text

2. **Municipality Lookup** (`municipality_lookup.py`)
   - Identifies relevant municipalities
   - Maintains database of supported jurisdictions
   - Provides municipal contact information

3. **Policy Retrieval** (`policy_retrieval.py`)
   - Retrieves zoning and land use information
   - Analyzes development requirements
   - Provides cottage development analysis

4. **Report Generator** (`report_generator.py`)
   - Creates professional PDF reports
   - Includes executive summary, analysis, and recommendations
   - Formatted for professional use

5. **Web Interface** (`app.py`, `templates/index.html`)
   - User-friendly web application
   - Real-time analysis and results display
   - PDF report generation

### Data Sources

The tool integrates with various Alberta land use data sources:
- Alberta Land-use Framework
- Municipal planning documents and bylaws
- Cadastral mapping data (Altalis)
- Municipal zoning databases

## API Endpoints

### POST `/api/analyze_property`
Analyze property and return land use information.

**Request Body:**
```json
{
  "address": "123 Main St, Red Deer, AB",
  "legal_description": "NE 12-45-26-W4M",
  "additional_info": "14.55 acres, cottage development planned"
}
```

**Response:**
```json
{
  "property_info": {...},
  "municipality_info": {...},
  "policy_info": {...},
  "feasibility_summary": {...}
}
```

### POST `/api/generate_report`
Generate PDF feasibility report.

### GET `/api/municipalities`
Get list of supported municipalities.

## 🔧 Configuration

### Environment Variables
Create a `.env` file for configuration:
```
FLASK_ENV=development
FLASK_DEBUG=True
```

### Extending Municipality Coverage
To add new municipalities, update the `municipalities_data` in `municipality_lookup.py`:

```python
"New Municipality": {
    "type": "city",
    "coordinates": {"lat": 53.0000, "lon": -113.0000},
    "website": "https://www.newmunicipality.ca",
    "planning_dept": "planning@newmunicipality.ca",
    "land_use_bylaw": "https://www.newmunicipality.ca/bylaws/",
    "contact_info": {
        "phone": "780-xxx-xxxx",
        "address": "123 Main St, New Municipality, AB"
    }
}
```

## Development Roadmap

### Phase 1 (Current)
-  Core property analysis functionality
- Basic municipality coverage (Red Deer to Athabasca)
-  PDF report generation
- Web interface

### Phase 2 (Future)
- [ ] Real-time municipal data integration
- [ ] Expanded provincial coverage
- [ ] Advanced development analysis (environmental, infrastructure)
- [ ] User accounts and project management
- [ ] Mobile application

### Phase 3 (Advanced)
- [ ] AI-powered policy interpretation
- [ ] Predictive development analysis
- [ ] Integration with provincial databases
- [ ] Multi-language support

## 🛠️ Customization

### Adding New Analysis Types
Extend the `PolicyRetrieval` class to add specialized analysis:

```python
def get_industrial_development_analysis(self, policy_info, property_details):
    # Custom analysis for industrial development
    pass
```

### Custom Report Templates
Modify `report_generator.py` to create custom report layouts:

```python
def create_custom_report_section(self, data):
    # Add custom sections to PDF reports
    pass
```

##  Important Disclaimers

1. **Preliminary Assessment Only**: This tool provides preliminary feasibility assessments based on available data. Always verify information with municipal authorities.

2. **Data Accuracy**: While we strive for accuracy, municipal policies and zoning can change. Always consult current bylaws and planning departments.

3. **Professional Consultation**: This tool does not replace professional planning, legal, or engineering advice. Consult qualified professionals for development decisions.

4. **Regulatory Compliance**: Users are responsible for ensuring compliance with all applicable laws, regulations, and municipal requirements.

## 📞 Support and Contact

For technical support or questions about the tool:
- Review the documentation and examples
- Check municipal websites for current policies
- Consult with local planning professionals

##  Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool provides preliminary feasibility assessments based on available data. Always verify information with municipal authorities before making development decisions. This tool does not constitute professional planning or legal advice.

## Support

- 📧 **Issues**: [GitHub Issues](https://github.com/eokusany/Land-use-feasibility-tool/issues)
- 📖 **Documentation**: See README and code comments
- 🌟 **Star this repo** if you find it useful!

## Acknowledgments

- Alberta municipalities for providing public land use data
- Flask and Python communities for excellent frameworks
- Contributors and users providing feedback

---

** Built for Alberta land developers and planners to streamline feasibility assessments and accelerate development planning.**

** Star this repository if it helps your land development projects!**
