import re
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from pydantic_yaml import parse_yaml_raw_as
from typing import Dict


class StringConfigs(BaseModel):
    strname_to_size: Dict[str, int] = Field(default_factory=lambda: {})

    @field_validator("strname_to_size")
    @classmethod
    def check_mappings(cls, val: Dict[str, int]):
        valid_var_regex = re.compile(r"[A-Z][A-Z_0-9]?")

        for key, sz in val.items():
            assert key.endswith("$") or key.endswith(
                "$()"
            ), f"{key} must end with a $ or $()"
            assert key == key.upper(), f"{key} must be all caps"
            var_only = key[: key.find("$")]
            assert 1 <= len(var_only) <= 2, f"{var_only} must be 1 or 2 characters"
            assert valid_var_regex.match(
                var_only
            ), f"{var_only} must be a valid BASIC name"
            assert 0 < sz < 32767, f"{sz} for {key} must be between 0 and 32767"
        return val


class CompilerConfigs(BaseModel):
    string_configs: StringConfigs = Field(default_factory=lambda: StringConfigs())

    @classmethod
    def load(cls, path: Path) -> "CompilerConfigs":
        with open(path) as handle:
            yaml = handle.read()
            return parse_yaml_raw_as(cls, yaml)
