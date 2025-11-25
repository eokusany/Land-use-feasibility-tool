#!/usr/bin/env python3
"""
Test script for the Alberta Land Use Tool using the sample property data
This demonstrates how the tool would analyze the cottage development property
"""

import json
from property_parser import PropertyParser
from municipality_lookup import MunicipalityLookup
from policy_retrieval import PolicyRetrieval
from report_generator import ReportGenerator

def test_sample_property():
    """Test the tool with the sample property from the email"""
    
    print("🏡 Alberta Land Use Feasibility Tool - Sample Property Test")
    print("=" * 60)
    
    # Sample data from the email
    sample_data = {
        "address": "Property north of Black Bull Golf, west of The Village at Pigeon Lake, AB",
        "legal_description": "14.55 acre rural commercial property",  # Would need actual legal description
        "additional_info": """
        14.55 acre rural commercial property directly North of Black Bull Golf and west of The Village at Pigeon Lake. 
        Plan to develop the north section of the property with small cottages for rent. The cottages would range 
        600-800sq ft per unit and ideally 4-5 cottages per acre. Start small (4-5 cottages) and develop the land 
        over the course of many years. The south (5+/- acres) should be something other than cottages.
        
        The county just installed a septic lift station to the north. The septic pipes and power line are in place 
        along the edge of our property. There's no village water, so everyone drills for it. The hwy has turning 
        lanes from both directions that lead onto the county road which accesses our property. There's a 
        ravine/creek along the eastern portion of the property.
        
        Neighbouring property to the north consist of .3 acre rv lots for sale.
        """
    }
    
    # Initialize components
    print("🔧 Initializing analysis components...")
    property_parser = PropertyParser()
    municipality_lookup = MunicipalityLookup()
    policy_retrieval = PolicyRetrieval()
    report_generator = ReportGenerator()
    
    try:
        # Step 1: Parse property information
        print("\n📍 Step 1: Parsing property information...")
        property_info = property_parser.parse_property_info(
            address=sample_data["address"],
            legal_description=sample_data["legal_description"],
            additional_info=sample_data["additional_info"]
        )
        
        if property_info:
            print("✅ Property information parsed successfully")
            print(f"   - Property details found: {len(property_info.get('property_details', {}))} characteristics")
            print(f"   - Municipality hints: {property_info.get('municipality_hints', [])}")
            if property_info.get('property_details', {}).get('acreage'):
                print(f"   - Acreage: {property_info['property_details']['acreage']} acres")
        else:
            print("❌ Failed to parse property information")
            return
        
        # Step 2: Lookup municipality
        print("\n🏛️ Step 2: Looking up municipality...")
        municipality_info = municipality_lookup.find_municipality(property_info)
        
        if municipality_info:
            print("✅ Municipality identified successfully")
            print(f"   - Municipality: {municipality_info.get('name', 'Unknown')}")
            print(f"   - Type: {municipality_info.get('type', 'Unknown')}")
            print(f"   - Website: {municipality_info.get('website', 'Not available')}")
        else:
            print("⚠️ Municipality not identified - using Wetaskiwin County as fallback")
            # Use fallback municipality for demonstration
            municipality_info = municipality_lookup._find_by_name("Wetaskiwin County")
        
        # Step 3: Retrieve policies and zoning
        print("\n📋 Step 3: Retrieving land use policies...")
        policy_info = policy_retrieval.get_land_use_policies(municipality_info, property_info)
        
        print("✅ Policy information retrieved")
        print(f"   - Zoning: {policy_info.get('zoning', 'Not determined')}")
        print(f"   - Permitted uses: {len(policy_info.get('permitted_uses', []))} found")
        print(f"   - Development requirements: {len(policy_info.get('development_requirements', []))} found")
        
        # Step 4: Cottage development analysis
        print("\n🏘️ Step 4: Analyzing cottage development potential...")
        cottage_analysis = policy_retrieval.get_cottage_development_analysis(
            policy_info, 
            property_info.get('property_details', {})
        )
        
        print("✅ Cottage development analysis completed")
        print(f"   - Feasibility: {cottage_analysis.get('feasibility', 'Unknown')}")
        
        cottage_potential = cottage_analysis.get('cottage_potential', {})
        if cottage_potential:
            print(f"   - Estimated cottage units: {cottage_potential.get('estimated_cottage_units', 'Unknown')}")
            print(f"   - Recommended Phase 1: {cottage_potential.get('recommended_phase_1', 'Unknown')} units")
        
        # Step 5: Compile results
        print("\n📊 Step 5: Compiling analysis results...")
        
        results = {
            'property_info': property_info,
            'municipality_info': municipality_info,
            'policy_info': policy_info,
            'cottage_analysis': cottage_analysis,
            'feasibility_summary': {
                'development_potential': cottage_analysis.get('feasibility', 'Unknown'),
                'key_considerations': cottage_analysis.get('regulatory_considerations', []),
                'recommended_actions': cottage_analysis.get('next_steps', [])
            }
        }
        
        # Display summary
        print("\n" + "=" * 60)
        print("📈 FEASIBILITY ANALYSIS SUMMARY")
        print("=" * 60)
        
        print(f"🏢 Municipality: {municipality_info.get('name', 'Not identified')}")
        print(f"🏗️ Development Potential: {cottage_analysis.get('feasibility', 'Unknown')}")
        print(f"📏 Property Size: {property_info.get('property_details', {}).get('acreage', 'Unknown')} acres")
        print(f"🏘️ Zoning: {policy_info.get('zoning', 'Not determined')}")
        
        if cottage_potential:
            print(f"🏠 Potential Cottage Units: {cottage_potential.get('estimated_cottage_units', 'Unknown')}")
            print(f"🚀 Phase 1 Recommendation: {cottage_potential.get('recommended_phase_1', 'Unknown')} units")
        
        print("\n🔑 Key Considerations:")
        for i, consideration in enumerate(cottage_analysis.get('regulatory_considerations', [])[:5], 1):
            print(f"   {i}. {consideration}")
        
        print("\n📋 Next Steps:")
        for i, step in enumerate(cottage_analysis.get('next_steps', [])[:3], 1):
            print(f"   {i}. {step}")
        
        # Step 6: Generate report (optional)
        print(f"\n📄 Step 6: Generating PDF report...")
        try:
            report_path = report_generator.create_report(results)
            print(f"✅ PDF report generated: {report_path}")
        except Exception as e:
            print(f"⚠️ Report generation failed: {str(e)}")
        
        print("\n" + "=" * 60)
        print("✅ Analysis completed successfully!")
        print("💡 This demonstrates how the tool would analyze your cottage development property.")
        print("🌐 Access the web interface at http://localhost:5000 for interactive analysis.")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        return None

if __name__ == "__main__":
    test_sample_property()
