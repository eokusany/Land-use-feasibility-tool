"""Dataclasses describing the Tier 1 parcel-context layer.

These augment `ZoningResult` with the lot/permit/overlay/aerial data shown in
the Parcel Context tab. They are deliberately separate from `ZoningResult` so
that a slow permits API never blocks the zone lookup itself.
"""

from dataclasses import asdict, dataclass, field
from typing import List, Optional


_OVERLAY_CATEGORIES = frozenset({"heritage", "flood", "slope", "airport", "other"})


@dataclass
class LotCharacteristics:
    """Lot area, frontage, depth, and approximate orientation."""

    area_m2: Optional[float]
    frontage_m: Optional[float]
    depth_m: Optional[float]
    orientation_deg: Optional[float]   # 0 = North, 90 = East. None when unknown.
    source: str
    source_url: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AdjacentZone:
    """A neighbouring zone summarised across the 100 m ring around the parcel."""

    code: str
    name: str
    count: int                          # how many polygons of this zone fall in the ring

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PermitRecord:
    """One open or recent development/building permit at the address."""

    permit_number: str
    issue_date: Optional[str]           # ISO YYYY-MM-DD when known
    status: Optional[str]
    work_type: Optional[str]
    description: Optional[str]
    source: str
    source_url: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class OverlayFlag:
    """A heritage/flood/slope/airport hazard or overlay that touches the parcel."""

    category: str                       # one of _OVERLAY_CATEGORIES
    code: str
    description: str
    source: str
    source_url: str

    def __post_init__(self):
        if self.category not in _OVERLAY_CATEGORIES:
            raise ValueError(
                f"OverlayFlag.category={self.category!r} not in {sorted(_OVERLAY_CATEGORIES)}"
            )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AerialImage:
    """A single static aerial image of the parcel (Mapbox)."""

    url: str
    width: int
    height: int
    zoom: int
    attribution: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ParcelContext:
    """All Tier 1 context layers for one parcel. Every field is optional —
    individual feature failures populate `warnings` instead of raising."""

    lot: Optional[LotCharacteristics] = None
    adjacent_zones: List[AdjacentZone] = field(default_factory=list)
    permits: List[PermitRecord] = field(default_factory=list)
    overlay_flags: List[OverlayFlag] = field(default_factory=list)
    aerial_image: Optional[AerialImage] = None
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "lot": self.lot.to_dict() if self.lot else None,
            "adjacent_zones": [a.to_dict() for a in self.adjacent_zones],
            "permits": [p.to_dict() for p in self.permits],
            "overlay_flags": [o.to_dict() for o in self.overlay_flags],
            "aerial_image": self.aerial_image.to_dict() if self.aerial_image else None,
            "warnings": list(self.warnings),
        }
