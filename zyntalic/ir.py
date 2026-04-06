from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Frame:
    id: str
    anchor: str
    weight: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "anchor": self.anchor,
            "weight": float(self.weight),
        }


class PivotType(str, Enum):
    DIVERGE = "diverge"
    CONVERGE = "converge"
    NEUTRAL = "neutral"


@dataclass
class SentenceSidecar:
    frames: List[Frame] = field(default_factory=list)
    pivot: PivotType = PivotType.NEUTRAL
    anchor_weights: List[Tuple[str, float]] = field(default_factory=list)
    sigil: Optional[str] = None
    sigil_type: Optional[str] = None
    evidentiality: Optional[str] = None
    tokens: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frames": [frame.to_dict() for frame in self.frames],
            "pivot": self.pivot.value,
            "anchor_weights": [
                {"name": name, "weight": float(weight)}
                for name, weight in self.anchor_weights
            ],
            "sigil": self.sigil,
            "sigil_type": self.sigil_type,
            "evidentiality": self.evidentiality,
            "tokens": self.tokens,
        }

    def to_legacy_str(self) -> str:
        parts: List[str] = [f"pivot={self.pivot.value}"]
        if self.frames:
            frame_blob = "|".join(
                f"{frame.id}:{frame.anchor}:{frame.weight:.3f}" for frame in self.frames
            )
            parts.append(f"frames={frame_blob}")
        if self.anchor_weights:
            anchor_blob = "|".join(
                f"{name}:{weight:.3f}" for name, weight in self.anchor_weights
            )
            parts.append(f"anchors={anchor_blob}")
        if self.sigil:
            parts.append(f"sigil={self.sigil}")
        if self.sigil_type:
            parts.append(f"sigil_type={self.sigil_type}")
        if self.evidentiality:
            parts.append(f"evidentiality={self.evidentiality}")
        return f"⟦ctx:{'; '.join(parts)}⟧"
