"""End-to-end Playwright smoke tests.

Covers the four user flows the project actually has:

  1. Homepage loads cleanly (no console errors, expected landmarks, a11y).
  2. /api/health returns the expected JSON.
  3. Empty-form submission surfaces the inline error region (a11y).
  4. Wizard succeeds end-to-end with a mocked /api/analyze_property
     response — also verifies that a malicious javascript: URL coming back
     from the API does NOT become an executable href (XSS regression).

Run:
    pytest tests_e2e/ -v
"""

from __future__ import annotations

import json

import pytest
from playwright.sync_api import Page, expect


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_FAKE_ANALYZE_RESPONSE = {
    "property_info": {
        "raw_input": {"address": "1 Sir Winston Churchill Sq"},
        "coordinates": {"latitude": 53.5444, "longitude": -113.4909},
    },
    "municipality_info": {
        "name": "Edmonton",
        "province": "AB",
        "province_name": "Alberta",
        "type": "city",
        "website": "https://www.edmonton.ca",
        "land_use_bylaw": "https://www.edmonton.ca/city_government/bylaws/zoning-bylaw",
        "planning_dept": "planning@edmonton.ca",
        "planning_act": "Municipal Government Act",
        "building_code": "Alberta Building Code",
        "contact_info": {"phone": "780-555-0100", "address": "1 Sir Winston Churchill Sq"},
    },
    "policy_info": {
        "verification_status": "verified",
        "verification_required": False,
        "verification_message": None,
        "zoning": "CCA — Core Commercial Arts Zone",
        "zoning_code": "CCA",
        "zoning_status": "Verified from City of Edmonton Open Data — Zoning Bylaw 20001",
        "zone_source": "City of Edmonton Open Data — Zoning Bylaw 20001",
        "zone_source_url": "https://data.edmonton.ca",
        "zone_retrieved_at": "2026-05-23T16:00:00+00:00",
        "zone_bylaw_section_url": "https://zoningbylaw.edmonton.ca/cca",
        "zone_overlays": [
            {"code": "DN", "description": "Downtown Special Area", "bylaw_no": "12800"},
        ],
        "zone_provider_notes": [],
        "permitted_uses": [],
        "discretionary_uses": [],
        "setbacks": {},
        "density_restrictions": {},
        "height_restrictions": {},
        "land_use_bylaw": {
            "url": "https://www.edmonton.ca/zoning-bylaw",
            "title": "Edmonton Land Use Bylaw",
        },
        "bylaw_links": ["https://www.edmonton.ca/zoning-bylaw"],
        "development_requirements": [
            "Development permit required for most new construction",
            "Compliance with Alberta Building Code",
        ],
        "verification_steps": [
            "Look up the parcel on the municipality's online zoning map.",
        ],
        "contact_info": {"phone": "780-555-0100", "address": "1 Sir Winston Churchill Sq"},
    },
    "feasibility_summary": {
        "development_potential": "Zone Verified — Bylaw Review Required",
        "key_considerations": ["Parcel zone: CCA — Core Commercial Arts Zone (verified)."],
        "recommended_actions": [
            "Read the bylaw section that governs this zone",
            "Engage a qualified land use planner",
        ],
    },
    "analysis_date": "2026-05-23T16:00:00",
    "request_id": "deadbeef",
}


def _mock_api(page: Page, payload: dict) -> None:
    """Replace /api/analyze_property with a canned JSON response."""
    page.route(
        "**/api/analyze_property",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(payload),
        ),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_homepage_loads_and_has_a11y_landmarks(page: Page, base_url: str):
    console_errors: list[str] = []
    page.on("console", lambda msg: msg.type == "error" and console_errors.append(msg.text))
    page.on("pageerror", lambda exc: console_errors.append(str(exc)))

    page.goto(base_url, wait_until="networkidle")

    # Title + branding (Plotline rebrand)
    expect(page).to_have_title("Plotline — Canadian zoning lookup & feasibility")

    # Skip link for keyboard users (a11y)
    expect(page.locator("a.skip-link")).to_be_attached()

    # <main> landmark
    expect(page.locator("main#mainContent")).to_be_visible()

    # Brand wordmark
    expect(page.locator(".cl-nav .brand .wordmark")).to_have_text("Plotline")

    # Stepper is a semantic list with aria-current on step 1
    stepper = page.locator(".wizard-stepper")
    expect(stepper).to_have_attribute("aria-label", "Workflow progress")
    expect(page.locator("#step1Btn")).to_have_attribute("aria-current", "step")

    # Province dropdown populated from /api/provinces
    province_select = page.locator("#provinceSelect")
    expect(province_select.locator("option")).to_have_count(14)  # 1 placeholder + 13 provinces

    # The province pills rendered as interactive buttons
    pills = page.locator("#provincePills .pill")
    expect(pills.first).to_be_visible()
    expect(pills).to_have_count(13)

    # The verified-province pill carries the .verified class so it's visually distinct
    ab_pill = page.locator("#provincePills .pill", has_text="AB")
    expect(ab_pill).to_have_class("pill verified")

    # The hero shows the verified-cities chip — this is the differentiator
    expect(page.locator(".verified-chip")).to_be_visible()
    expect(page.locator(".verified-chip")).to_contain_text("Edmonton")

    # No JS errors on initial load
    assert console_errors == [], f"Unexpected console errors: {console_errors}"


def test_health_endpoint_returns_expected_shape(page: Page, base_url: str):
    resp = page.request.get(f"{base_url}/api/health")
    assert resp.status == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "canland"
    assert set(body["providers_registered"]) >= {"calgary", "edmonton"}
    assert body["municipalities"] > 0
    assert "http_cache_enabled" in body


def test_empty_submission_surfaces_inline_error(page: Page, base_url: str):
    page.goto(base_url, wait_until="networkidle")
    # Submit with nothing filled
    page.locator("#analyzeBtn").click()
    err = page.locator("#cl-error")
    expect(err).to_be_visible()
    # Properly tagged as an alert region (a11y)
    expect(err).to_have_attribute("role", "alert")
    # Message is the client-side validation, not raw server text
    expect(err).to_contain_text("street address")


def test_sample_button_prefills_and_submits(page: Page, base_url: str):
    """The 'Try this address' button should auto-fill the form with the
    Edmonton demo and submit. Verifies the demo loop works end-to-end."""
    _mock_api(page, _FAKE_ANALYZE_RESPONSE)

    page.goto(base_url, wait_until="networkidle")
    page.locator("#tryDemoBtn").click()

    # Form should now be populated and the results panel reached
    expect(page.locator("#addressInput")).to_have_value(
        "1 Sir Winston Churchill Square, Edmonton, AB"
    )
    expect(page.locator("#panelStep3")).to_be_visible()
    expect(page.locator("#resVerifiedZoneCode")).to_contain_text("CCA")


def test_province_pill_selects_dropdown(page: Page, base_url: str):
    """Clicking a province pill should populate the province dropdown
    and trigger the city cascade."""
    page.goto(base_url, wait_until="networkidle")
    page.locator("#provincePills .pill", has_text="AB").click()

    # Dropdown should now have AB selected
    expect(page.locator("#provinceSelect")).to_have_value("AB")
    # City dropdown should populate (no longer disabled, has options)
    expect(page.locator("#citySelect")).not_to_be_disabled()
    expect(page.locator("#citySelect option", has_text="Edmonton")).to_be_attached()


def test_wizard_renders_verified_zone_and_resists_xss(page: Page, base_url: str):
    """End-to-end happy path. Also passes a malicious javascript:* URL in
    the mocked response — the page MUST NOT render it as a clickable href."""
    payload = json.loads(json.dumps(_FAKE_ANALYZE_RESPONSE))  # deep copy
    # Inject a malicious URL where the UI would normally interpolate a link.
    payload["municipality_info"]["website"] = "javascript:fetch('/api/health')"
    _mock_api(page, payload)

    page.goto(base_url, wait_until="networkidle")
    page.locator("#addressInput").fill("1 Sir Winston Churchill Sq")
    page.locator("#analyzeBtn").click()

    # The results panel appears
    expect(page.locator("#panelStep3")).to_be_visible()
    # Verified-zone block is shown (verified path)
    expect(page.locator("#resVerifiedZoneBlock")).to_be_visible()
    expect(page.locator("#resVerifiedZoneCode")).to_contain_text("CCA")
    # Stepper now marks step 3 as current
    expect(page.locator("#step3Btn")).to_have_attribute("aria-current", "step")
    # Bylaw link rendered safely with rel attributes
    bylaw_link = page.locator("#resVerifiedBylawLink a")
    expect(bylaw_link).to_have_attribute("rel", "noopener noreferrer")
    expect(bylaw_link).to_have_attribute("target", "_blank")

    # XSS guard: the malicious javascript: URL must NOT be in any href on the
    # page. The UI's safeUrl() helper should have rejected it.
    all_hrefs = page.locator("a").evaluate_all("els => els.map(el => el.getAttribute('href'))")
    for href in all_hrefs:
        if href is None:
            continue
        assert not href.lower().startswith("javascript:"), \
            f"XSS regression: javascript: URL rendered as href: {href!r}"
