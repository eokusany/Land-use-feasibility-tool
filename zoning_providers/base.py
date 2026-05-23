"""Base interface and shared infrastructure for parcel-level zoning providers."""

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import List, Optional

import requests


class ProviderError(Exception):
    """Raised when a provider cannot be reached or returns malformed data.

    PolicyRetrieval catches this and falls back to verification-required mode.
    The error message is surfaced to the user so they know they're not seeing
    verified data.
    """


@dataclass
class ZoningOverlay:
    """An overlay zone applying on top of the base zone (heritage, airport, etc.)."""

    code: str
    description: str
    bylaw_no: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ZoningResult:
    """A successful parcel-level zoning lookup."""

    # Required: what the city says about this parcel
    zone_code: str
    zone_name: str

    # Source attribution — must always be present so the user can verify
    source: str
    source_url: str
    retrieved_at: str

    bylaw_section_url: Optional[str] = None
    overlays: List[ZoningOverlay] = field(default_factory=list)
    provider_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class ZoningProvider(ABC):
    """
    Base class for per-municipality zoning lookups.

    Subclasses MUST set the class attributes below and implement `lookup`.
    The shared `_get_json` helper handles common HTTP/JSON pitfalls so each
    new provider doesn't have to re-implement error handling.
    """

    name: str = ""
    municipality: str = ""
    province: str = ""
    source: str = ""
    source_url: str = ""

    # Network timeout in seconds. Kept tight so a slow city API doesn't
    # block the entire CanLand request — the user can always retry.
    timeout: float = 8.0

    # Default User-Agent for outbound requests
    _USER_AGENT = "canland_feasibility_tool/1.0"

    @abstractmethod
    def lookup(self, lat: float, lon: float) -> Optional[ZoningResult]:
        """
        Look up the zoning at the given WGS84 coordinate.

        Returns:
            ZoningResult on a successful hit.
            None when the coordinate is outside the municipality.

        Raises:
            ProviderError on network failures, malformed responses, or
            unexpected upstream errors.
        """

    # ------------------------------------------------------------------
    # Shared HTTP helper
    # ------------------------------------------------------------------

    def _get_json(self, url: str, params: dict, *, expect: str = "list"):
        """Issue a GET request and return parsed JSON, raising ProviderError
        on any failure mode the caller would otherwise have to handle by hand.

        Args:
            url: Fully-qualified endpoint URL.
            params: Querystring parameters.
            expect: "list" to require a JSON array response (Socrata default)
                    or "json" to accept any well-formed JSON shape.
        """
        try:
            resp = requests.get(
                url,
                params=params,
                timeout=self.timeout,
                headers={
                    "Accept": "application/json",
                    "User-Agent": self._USER_AGENT,
                },
            )
        except requests.RequestException as exc:
            raise ProviderError(
                f"{self.municipality} zoning API unreachable: {exc}"
            ) from exc

        if resp.status_code != 200:
            raise ProviderError(
                f"{self.municipality} zoning API returned HTTP "
                f"{resp.status_code} for {url}"
            )

        try:
            data = resp.json()
        except ValueError as exc:
            raise ProviderError(
                f"{self.municipality} zoning API returned non-JSON response: {exc}"
            ) from exc

        if isinstance(data, dict) and data.get("error"):
            raise ProviderError(
                f"{self.municipality} zoning API error: "
                f"{data.get('message', data)}"
            )

        if expect == "list" and not isinstance(data, list):
            raise ProviderError(
                f"{self.municipality} zoning API returned unexpected shape: "
                f"{type(data).__name__}"
            )

        return data
