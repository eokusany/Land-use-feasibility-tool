"""Plotline Flask application — entrypoint and HTTP routes."""

import logging
import os
import sys
import time
import uuid
from datetime import datetime

from flask import Flask, g, jsonify, render_template, request, send_file

from http_cache import install_http_cache_if_configured
from municipality_lookup import MunicipalityLookup
from policy_retrieval import PolicyRetrieval
from property_parser import PropertyParser
from report_generator import ReportGenerator

# Install the shared HTTP cache for municipal API calls *before* any provider
# imports its requests session. No-op unless CANLAND_HTTP_CACHE_PATH is set.
install_http_cache_if_configured()


# ---------------------------------------------------------------------------
# Logging — structured-ish, stdout-friendly so Render captures it cleanly
# ---------------------------------------------------------------------------

LOG_LEVEL = os.environ.get("CANLAND_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s [%(request_id)s] %(message)s",
    stream=sys.stdout,
)


class _RequestIdFilter(logging.Filter):
    def filter(self, record):  # noqa: D401
        record.request_id = getattr(g, "request_id", "-") if _has_app_context() else "-"
        return True


def _has_app_context():
    try:
        from flask import has_app_context

        return has_app_context()
    except Exception:  # noqa: BLE001
        return False


for _h in logging.getLogger().handlers:
    _h.addFilter(_RequestIdFilter())

logger = logging.getLogger("canland.app")


# ---------------------------------------------------------------------------
# App + service singletons
# ---------------------------------------------------------------------------

app = Flask(__name__)

property_parser = PropertyParser()
municipality_lookup = MunicipalityLookup()
policy_retrieval = PolicyRetrieval()
report_generator = ReportGenerator()


@app.before_request
def _attach_request_id():
    g.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    g.t_start = time.perf_counter()


@app.after_request
def _log_response(response):
    try:
        elapsed_ms = round((time.perf_counter() - g.t_start) * 1000, 1)
    except Exception:  # noqa: BLE001 — defensive
        elapsed_ms = -1
    logger.info(
        "%s %s -> %s in %sms",
        request.method,
        request.path,
        response.status_code,
        elapsed_ms,
    )
    response.headers["X-Request-ID"] = getattr(g, "request_id", "-")
    return response


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health")
def health():
    """Liveness/readiness check. Returns provider registry size so deploys can
    confirm the import graph loaded cleanly."""
    from zoning_providers import PROVIDERS

    http_cache_active = bool(os.environ.get("CANLAND_HTTP_CACHE_PATH"))
    return jsonify(
        {
            "status": "ok",
            "service": "canland",
            "providers_registered": sorted(PROVIDERS.keys()),
            "municipalities": len(municipality_lookup.get_supported_municipalities()),
            "http_cache_enabled": http_cache_active,
            "time": datetime.utcnow().isoformat() + "Z",
        }
    )


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
        data = request.get_json(silent=True) or {}

        province = (data.get("province") or "").strip()
        city = (data.get("city") or "").strip()

        property_info = property_parser.parse_property_info(
            address=data.get("address", ""),
            legal_description=data.get("legal_description", ""),
            additional_info=data.get("additional_info", ""),
            province=province,
        )

        if not property_info:
            return (
                jsonify(
                    {
                        "error": "Unable to parse property information. "
                        "Please provide an address or description."
                    }
                ),
                400,
            )

        # Prefer explicit city/province selection from the UI
        if city and province:
            municipality_info = municipality_lookup.find_by_province_and_city(province, city)
        else:
            municipality_info = municipality_lookup.find_municipality(
                property_info, province_hint=province or None
            )

        if not municipality_info:
            return (
                jsonify(
                    {
                        "error": "Municipality not found. Try selecting a province and "
                        "city from the dropdowns, or check your address."
                    }
                ),
                404,
            )

        policy_info = policy_retrieval.get_land_use_policies(municipality_info, property_info)

        results = {
            "property_info": property_info,
            "municipality_info": municipality_info,
            "policy_info": policy_info,
            "analysis_date": datetime.now().isoformat(),
            "feasibility_summary": _generate_feasibility_summary(policy_info),
            "request_id": getattr(g, "request_id", None),
        }

        return jsonify(results)

    except Exception:  # noqa: BLE001 — sanitise raw exception text from the client
        logger.exception("analyze_property failed")
        return (
            jsonify(
                {
                    "error": "Internal error while analyzing property. "
                    "The incident has been logged.",
                    "request_id": getattr(g, "request_id", None),
                }
            ),
            500,
        )


@app.route("/api/generate_report", methods=["POST"])
def generate_report():
    try:
        data = request.get_json(silent=True) or {}
        report_path = report_generator.create_report(data)
        return send_file(
            report_path,
            as_attachment=True,
            download_name=f"canland_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        )
    except Exception:  # noqa: BLE001
        logger.exception("generate_report failed")
        return (
            jsonify(
                {
                    "error": "Internal error while generating the report.",
                    "request_id": getattr(g, "request_id", None),
                }
            ),
            500,
        )


@app.route("/api/municipalities")
def get_municipalities():
    return jsonify(municipality_lookup.get_supported_municipalities())


# ---------------------------------------------------------------------------
# Feasibility summary
# ---------------------------------------------------------------------------


def _generate_feasibility_summary(policy_info: dict) -> dict:
    """
    Build a summary that reflects what we actually know.

    Two modes:
      - verified:   a zoning provider returned a real zone code from the
                    city's open-data API. We name the zone but still don't
                    fabricate setbacks/height/uses — those live in bylaw text.
      - unverified: no provider available, geocoding failed, or provider
                    errored. Same Option-A behaviour as before.
    """
    province = policy_info.get("province") or ""
    bylaw = policy_info.get("land_use_bylaw") or {}
    bylaw_url = bylaw.get("url")
    status = policy_info.get("verification_status", "unverified")

    if status == "verified":
        zone = policy_info.get("zoning") or "Unknown"
        source = policy_info.get("zone_source") or "the city's open data"
        section_url = policy_info.get("zone_bylaw_section_url")
        overlays = policy_info.get("zone_overlays") or []

        key_considerations = [
            f"Parcel zone: {zone} (verified from {source}).",
            "Plotline does not extract setbacks, height limits, density, or permitted uses from bylaw text. "
            "Open the linked bylaw section for the authoritative rules.",
        ]
        if overlays:
            overlay_str = ", ".join(f"{o['code']} ({o['description']})" for o in overlays)
            key_considerations.append(f"Overlays in effect: {overlay_str}")
        for note in policy_info.get("zone_provider_notes") or []:
            key_considerations.append(note)

        recommended_actions = []
        if section_url:
            recommended_actions.append(f"Read the bylaw section that governs this zone: {section_url}")
        recommended_actions += [
            "Confirm any site-specific amendments or discretionary variances with the municipality",
            "Contact the municipal planning department for site-specific guidance",
            f"Confirm compliance with {province} provincial planning legislation"
            if province
            else "Confirm compliance with provincial planning legislation",
            "Engage a qualified land use planner before making development decisions",
        ]

        return {
            "development_potential": "Zone Verified — Bylaw Review Required",
            "key_considerations": key_considerations,
            "recommended_actions": recommended_actions,
        }

    # --- Unverified path (Option A behaviour) ---
    key_considerations = [
        "Parcel-level zoning has NOT been retrieved by this tool — it must be confirmed with the municipal planning department.",
        "Setbacks, height limits, density, and permitted uses depend on the specific zone designation and cannot be assumed from the address alone.",
    ]
    if policy_info.get("verification_message"):
        key_considerations.insert(0, policy_info["verification_message"])
    if bylaw_url:
        key_considerations.append(f"Reference the current land use bylaw: {bylaw_url}")

    recommended_actions = [
        "Look up the parcel on the municipality's online zoning map",
        "Contact the municipal planning department to confirm the current zone designation",
        "Request a Letter of Compliance or Zoning Memo for the legal title",
        f"Confirm compliance with {province} provincial planning legislation"
        if province
        else "Confirm compliance with provincial planning legislation",
        "Engage a qualified land use planner before making development decisions",
    ]

    return {
        "development_potential": "Verification Required",
        "key_considerations": key_considerations,
        "recommended_actions": recommended_actions,
    }


if __name__ == "__main__":
    os.makedirs("reports", exist_ok=True)
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_ENV", "development") == "development"
    app.run(debug=debug, host="0.0.0.0", port=port, use_reloader=False)
