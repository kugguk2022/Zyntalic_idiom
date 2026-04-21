from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


@dataclass(frozen=True)
class Frame:
    id: str
    anchor: str
    weight: float

    def to_dict(self) -> dict[str, Any]:
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
    frames: list[Frame] = field(default_factory=list)
    pivot: PivotType = PivotType.NEUTRAL
    anchor_weights: list[tuple[str, float]] = field(default_factory=list)
    anchor_mode: str | None = None
    selected_anchors: list[str] = field(default_factory=list)
    sigil: str | None = None
    sigil_type: str | None = None
    evidentiality: str | None = None
    register: str | None = None
    dialect: str | None = None
    scope_signature: str | None = None
    tokens: list[dict[str, Any]] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "frames": [frame.to_dict() for frame in self.frames],
            "pivot": self.pivot.value,
            "anchor_weights": [
                {"name": name, "weight": float(weight)}
                for name, weight in self.anchor_weights
            ],
            "anchor_mode": self.anchor_mode,
            "selected_anchors": list(self.selected_anchors),
            "sigil": self.sigil,
            "sigil_type": self.sigil_type,
            "evidentiality": self.evidentiality,
            "register": self.register,
            "dialect": self.dialect,
            "scope_signature": self.scope_signature,
            "tokens": self.tokens,
        }

    def to_legacy_str(self) -> str:
        parts: list[str] = [f"pivot={self.pivot.value}"]
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
        if self.anchor_mode:
            parts.append(f"anchor_mode={self.anchor_mode}")
        if self.selected_anchors:
            parts.append(f"selected={ '|'.join(self.selected_anchors[:4]) }")
        if self.sigil:
            parts.append(f"sigil={self.sigil}")
        if self.sigil_type:
            parts.append(f"sigil_type={self.sigil_type}")
        if self.evidentiality:
            parts.append(f"evidentiality={self.evidentiality}")
        if self.register:
            parts.append(f"register={self.register}")
        if self.dialect:
            parts.append(f"dialect={self.dialect}")
        if self.scope_signature:
            parts.append(f"scope={self.scope_signature}")
        return f"⟦ctx:{'; '.join(parts)}⟧"
