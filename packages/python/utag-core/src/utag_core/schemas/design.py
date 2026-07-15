"""UDC design schemas: design.yaml contract, tokens, components, CSS variables."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field

from utag_core.schemas import SLUG, StrictSchema


class ContrastLevel(str, Enum):
    AA = "AA"
    AAA = "AAA"


class Brand(StrictSchema):
    name: str = Field(min_length=1)
    voice: str = ""


class DesignTokens(StrictSchema):
    color: dict[str, str] = {}
    spacing: dict[str, str] = {}
    radius: dict[str, str] = {}
    typography: dict[str, str] = {}
    shadow: dict[str, str] = {}
    motion: dict[str, str] = {}


class VariantSpec(StrictSchema):
    id: str = Field(pattern=SLUG)
    props: dict[str, Any] = {}


class ComponentSpec(StrictSchema):
    id: str = Field(pattern=SLUG)
    type: str = Field(pattern=SLUG)
    props: dict[str, Any] = {}
    variants: list[VariantSpec] = []
    states: list[str] = []


class LayoutSpec(StrictSchema):
    id: str = Field(pattern=SLUG)
    regions: list[str] = Field(min_length=1)


class RouteSpec(StrictSchema):
    path: str = Field(pattern=r"^/")
    layout: str = Field(pattern=SLUG)
    components: list[str] = []


class InteractionSpec(StrictSchema):
    id: str = Field(pattern=SLUG)
    source: str = Field(pattern=SLUG)
    target: str = Field(pattern=SLUG)


class DataBindingSpec(StrictSchema):
    id: str = Field(pattern=SLUG)
    resource: str = Field(min_length=1)
    component: str = Field(pattern=SLUG)


class DataSection(StrictSchema):
    resources: list[str] = []
    bindings: list[DataBindingSpec] = []
    #: resource name -> schema kind (e.g. runs: run-trace); typed data props,
    #: TS contract emission, and fixture generation all key off this
    contracts: dict[str, str] = {}


class ThemeSpec(StrictSchema):
    name: str = Field(pattern=SLUG)
    tokens: dict[str, str] = {}


class AccessibilityContract(StrictSchema):
    minContrast: ContrastLevel
    keyboardRequired: bool


class DesignYaml(StrictSchema):
    """Canonical design source-of-truth (design.yaml)."""
    id: str = Field(pattern=SLUG)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    brand: Brand
    tokens: DesignTokens = DesignTokens()
    themes: dict[str, dict[str, str]] = {}
    components: list[ComponentSpec] = []
    layouts: list[LayoutSpec] = []
    routes: list[RouteSpec] = []
    interactions: list[InteractionSpec] = []
    data: DataSection = DataSection()
    accessibility: AccessibilityContract


class DesignTokenDocument(StrictSchema):
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    tokens: DesignTokens


class CssVariable(StrictSchema):
    name: str = Field(pattern=r"^--[a-z][a-z0-9-]*$")
    value: str = Field(min_length=1)


class CssVariableManifest(StrictSchema):
    file: str = Field(min_length=1)
    variables: list[CssVariable]
    source_design: str = Field(pattern=SLUG)


TOP_LEVEL = [
    DesignYaml, DesignTokenDocument, ComponentSpec, VariantSpec, LayoutSpec,
    RouteSpec, InteractionSpec, DataBindingSpec, ThemeSpec, CssVariableManifest,
    AccessibilityContract,
]

EXAMPLES = {
    "DesignYaml": {
        "id": "utag-console", "version": "1.0.0",
        "brand": {"name": "UTAG", "voice": "verification-first"},
        "tokens": {"color": {"bg": "#0b0d10", "fg": "#e6e8ea"}, "spacing": {"1": "4px"}},
        "themes": {"dark": {"bg": "#0b0d10"}},
        "components": [{"id": "run-status-card", "type": "card", "props": {}, "variants": [], "states": ["idle"]}],
        "layouts": [{"id": "console-shell", "regions": ["sidebar", "header", "main", "inspector"]}],
        "routes": [{"path": "/runs", "layout": "console-shell", "components": ["run-status-card"]}],
        "interactions": [{"id": "select-run", "source": "run-status-card", "target": "run-status-card"}],
        "data": {"resources": ["runs"], "contracts": {"runs": "run-trace"}},
        "accessibility": {"minContrast": "AA", "keyboardRequired": True},
    },
    "DesignTokenDocument": {"version": "1.0.0", "tokens": {"color": {"bg": "#0b0d10"}}},
    "ComponentSpec": {"id": "run-status-card", "type": "card", "props": {"title": "Run"},
                      "variants": [{"id": "compact", "props": {"dense": True}}], "states": ["idle", "loading"]},
    "VariantSpec": {"id": "compact", "props": {"dense": True}},
    "LayoutSpec": {"id": "console-shell", "regions": ["sidebar", "main"]},
    "RouteSpec": {"path": "/runs", "layout": "console-shell", "components": ["run-status-card"]},
    "InteractionSpec": {"id": "select-run", "source": "run-table", "target": "run-inspector"},
    "DataBindingSpec": {"id": "runs-bind", "resource": "runs", "component": "run-status-card"},
    "ThemeSpec": {"name": "dark", "tokens": {"bg": "#0b0d10"}},
    "CssVariableManifest": {"file": "theme.css", "source_design": "utag-console",
                            "variables": [{"name": "--color-bg", "value": "#0b0d10"}]},
    "AccessibilityContract": {"minContrast": "AA", "keyboardRequired": True},
}
