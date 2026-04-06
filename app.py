from flask import Flask, render_template, request, jsonify, send_file
import os
from datetime import datetime
from property_parser import PropertyParser
from municipality_lookup import MunicipalityLookup
from policy_retrieval import PolicyRetrieval
from report_generator import ReportGenerator

app = Flask(__name__)

property_parser = PropertyParser()
municipality_lookup = MunicipalityLookup()
policy_retrieval = PolicyRetrieval()
report_generator = ReportGenerator()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/provinces")
def get_provinces():
    """Return all supported Canadian provinces and territories."""
    return jsonify(municipality_lookup.get_supported_provinces())


@app.route("/api/cities/<province_code>")
def get_cities(province_code):
    """Return cities for a given province code."""
    cities = municipality_lookup.get_cities_for_province(province_code)
    return jsonify(cities)


@app.route("/api/analyze_property", methods=["POST"])
def analyze_property():
    try:
        data = request.get_json()

        province = data.get("province", "")
        city = data.get("city", "")

        property_info = property_parser.parse_property_info(
            address=data.get("address", ""),
            legal_description=data.get("legal_description", ""),
            additional_info=data.get("additional_info", ""),
            province=province,
        )

        if not property_info:
            return jsonify({"error": "Unable to parse property information. Please provide an address or description."}), 400

        # Prefer explicit city/province selection from the UI
        if city and province:
            municipality_info = municipality_lookup.find_by_province_and_city(province, city)
        else:
            municipality_info = municipality_lookup.find_municipality(property_info, province_hint=province or None)

        if not municipality_info:
            return jsonify({
                "error": "Municipality not found. Try selecting a province and city from the dropdowns, or check your address."
            }), 404

        policy_info = policy_retrieval.get_land_use_policies(municipality_info, property_info)

        results = {
            "property_info": property_info,
            "municipality_info": municipality_info,
            "policy_info": policy_info,
            "analysis_date": datetime.now().isoformat(),
            "feasibility_summary": _generate_feasibility_summary(policy_info),
        }

        return jsonify(results)

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/generate_report", methods=["POST"])
def generate_report():
    try:
        data = request.get_json()
        report_path = report_generator.create_report(data)
        return send_file(
            report_path,
            as_attachment=True,
            download_name=f"canland_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/municipalities")
def get_municipalities():
    return jsonify(municipality_lookup.get_supported_municipalities())


def _generate_feasibility_summary(policy_info: dict) -> dict:
    summary = {
        "development_potential": "Unknown",
        "key_considerations": [],
        "recommended_actions": [],
    }

    zone_cat = policy_info.get("zone_category", "")
    zoning = policy_info.get("zoning", "") or ""

    if zone_cat in ("residential_low", "residential_high", "commercial", "rural_commercial"):
        summary["development_potential"] = "High"
    elif zone_cat in ("rural",):
        summary["development_potential"] = "Moderate"
    elif zone_cat == "industrial":
        summary["development_potential"] = "Moderate"
    else:
        # Fallback — check text
        if any(t in zoning.lower() for t in ["residential", "commercial", "mixed"]):
            summary["development_potential"] = "High"
        elif any(t in zoning.lower() for t in ["agricultural", "rural"]):
            summary["development_potential"] = "Moderate"
        else:
            summary["development_potential"] = "Low"

    setbacks = policy_info.get("setbacks", {})
    if setbacks:
        summary["key_considerations"].append(
            f"Setback requirements — front: {setbacks.get('front', 'N/A')}, "
            f"rear: {setbacks.get('rear', 'N/A')}, side: {setbacks.get('side', 'N/A')}"
        )

    density = policy_info.get("density_restrictions", {})
    if density.get("maximum_site_coverage"):
        summary["key_considerations"].append(
            f"Maximum site coverage: {density['maximum_site_coverage']}"
        )

    if policy_info.get("special_provisions"):
        summary["key_considerations"].extend(policy_info["special_provisions"])

    summary["recommended_actions"] = [
        "Consult with the municipal planning department",
        "Review the detailed land use bylaw for this zone",
        f"Confirm compliance with {policy_info.get('province', '')} provincial planning legislation",
        "Commission an environmental assessment if required",
        "Verify utility availability and service capacity",
    ]

    return summary


if __name__ == "__main__":
    os.makedirs("reports", exist_ok=True)
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_ENV", "development") == "development"
    app.run(debug=debug, host="0.0.0.0", port=port, use_reloader=False)
