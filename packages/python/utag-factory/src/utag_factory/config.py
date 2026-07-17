"""Load the canonical autoscaling profile and resolve runtime settings.

`policies/autoscaling.yaml` is the single source of truth; nothing here invents
defaults that contradict it. Profile selection: the env var the template names
(`selection.active_profile_env`), falling back to `selection.default_profile`.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from utag_core.schemas.factory import AutoscalingProfile, WorkerProfile

_DURATION = re.compile(r"^(\d+)(ms|s|m|h)$")
_BYTESIZE = re.compile(r"^(\d+)(B|KiB|MiB|GiB)$")
_DUR_FACTOR = {"ms": 0.001, "s": 1.0, "m": 60.0, "h": 3600.0}
_SIZE_FACTOR = {"B": 1, "KiB": 1024, "MiB": 1024**2, "GiB": 1024**3}


def parse_duration_s(text: str) -> float:
    m = _DURATION.match(text)
    if not m:
        raise ValueError(f"not a duration: {text!r}")
    return int(m.group(1)) * _DUR_FACTOR[m.group(2)]


def parse_bytes(text: str) -> int:
    m = _BYTESIZE.match(text)
    if not m:
        raise ValueError(f"not a byte size: {text!r}")
    return int(m.group(1)) * _SIZE_FACTOR[m.group(2)]


@dataclass
class FactoryConfig:
    profile: AutoscalingProfile
    active_profile_name: str
    root: Path

    @property
    def worker_profile(self) -> WorkerProfile:
        return self.profile.profiles[self.active_profile_name]

    @property
    def redis_url(self) -> str:
        return os.environ.get(self.profile.queue.connection_env, "redis://localhost:6379/0")

    @property
    def streams(self):
        return self.profile.queue.streams

    def data_dir(self) -> Path:
        d = Path(os.environ.get("UTAG_FACTORY_DATA", self.root / ".utag" / "factory"))
        d.mkdir(parents=True, exist_ok=True)
        return d


def load_config(root: Path | None = None) -> FactoryConfig:
    root = Path(root) if root is not None else Path.cwd()
    path = root / "policies" / "autoscaling.yaml"
    profile = AutoscalingProfile.model_validate(yaml.safe_load(path.read_text()))
    if profile.template.status != "canonical":
        raise ValueError(f"{path}: template status is {profile.template.status!r}, not canonical")
    name = os.environ.get(profile.selection.active_profile_env,
                          profile.selection.default_profile)
    if name not in profile.profiles:
        raise ValueError(f"unknown autoscaling profile {name!r}; "
                         f"known: {sorted(profile.profiles)}")
    return FactoryConfig(profile=profile, active_profile_name=name, root=root)
