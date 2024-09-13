import pytest
from pathlib import Path
from pydantic import ValidationError

from coco.b09 import configs


@pytest.fixture
def simple_config_path() -> Path:
    return Path(__file__).parent / "fixtures" / "simple-config.yaml"


@pytest.mark.parametrize(
    "var, sz",
    [
        ["A$", 1],
        ["B1$", 100],
        ["B$()", 22],
        ["B1$()", 33],
        ["B_$", 133],
    ],
)
def test_validates_valid_string_configs(var: str, sz: int) -> None:
    strname_to_size = {var: sz}
    str_config = configs.StringConfigs(strname_to_size=strname_to_size)
    assert str_config.strname_to_size == strname_to_size


@pytest.mark.parametrize(
    "var, sz",
    [
        ["_A$", 1],
        ["AAA$", 1],
        ["9A$", 1],
        ["A()$", 1],
        ["()A$", 1],
        ["A$", 0],
        ["A$", 32767],
        ["A", 3],
    ],
)
def test_fails_invalid_string_configs(var: str, sz: int) -> None:
    strname_to_size = {var: sz}
    with pytest.raises(ValidationError):
        configs.StringConfigs(strname_to_size=strname_to_size)


def test_loads_from_yaml(simple_config_path: Path) -> None:
    compiler_configs = configs.CompilerConfigs.load(simple_config_path)
    assert compiler_configs.string_configs.strname_to_size == {
        "A$": 100,
        "A$()": 200,
        "BC$": 300,
    }


def test_compiler_config_defaults() -> None:
    assert (
        configs.CompilerConfigs().string_configs.model_dump()
        == configs.StringConfigs().model_dump()
    )


def test_string_config_defaults() -> None:
    str_config = configs.StringConfigs()
    assert len(str_config.strname_to_size) == 0
