"""
Base interface and types for parcel-level zoning providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import List, Optional


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
    source: str            # human-readable: "City of Edmonton Open Data — Zoning Bylaw 20001"
    source_url: str        # link to the dataset/portal
    retrieved_at: str      # ISO 8601 timestamp

    # Optional richer fields
    bylaw_section_url: Optional[str] = None    # deep link into the bylaw text for THIS zone
    overlays: List[ZoningOverlay] = field(default_factory=list)

    # Notes the provider wants the user to see (e.g. "DC2 zones are
    # site-specific — read the bylaw for the actual rules")
    provider_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["overlays"] = [o for o in d["overlays"]]  # already dicts via asdict
        return d


class ZoningProvider(ABC):
    """
    Base class for per-municipality zoning lookups.

    Subclasses MUST set the class attributes below and implement `lookup`.
    """

    name: str = ""              # short identifier, e.g. "edmonton"
    municipality: str = ""      # display name, e.g. "Edmonton"
    province: str = ""          # 2-letter province code, e.g. "AB"
    source: str = ""            # human-readable source string
    source_url: str = ""        # link to the dataset/portal

    # Network timeout in seconds. Kept tight so a slow city API doesn't
    # block the entire CanLand request — the user can always retry.
    timeout: float = 8.0

    @abstractmethod
    def lookup(self, lat: float, lon: float) -> Optional[ZoningResult]:
        """
        Look up the zoning at the given WGS84 coordinate.

        Returns:
            ZoningResult on a successful hit.
            None when the coordinate is outside the municipality (no polygon match).

        Raises:
            ProviderError on network failures, malformed responses, or
            unexpected upstream errors. Callers should catch this and fall
            back to verification-required mode.
        """
