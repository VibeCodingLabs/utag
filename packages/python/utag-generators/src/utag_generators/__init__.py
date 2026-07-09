"""utag-generators: model backends + artifact target generators + validators + meta."""
from utag_generators import validators  # noqa: F401  (registers validators)
from utag_generators.targets import (  # noqa: F401  (registers generators)
    agent_skill, design_md, go_harness, openapi_doc, prompt_yaml, pydantic_models, zod,
)
from utag_generators import meta  # noqa: F401  (registers generator-generator)

__version__ = "2.0.0"
