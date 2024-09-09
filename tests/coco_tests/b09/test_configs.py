import pytest
from pydantic import ValidationError

from coco.b09 import configs


@pytest.mark.parametrize(
    'var, sz',
    [
        ['A$', 1],
        ['B1$', 100],
        ['B$()', 22],
        ['B1$()', 33],
        ['B_$', 133],
    ],
)
def test_validates_valid_string_configs(var: str, sz: int):
    strname_to_size = {var: sz}
    str_config = configs.StringConfigs(strname_to_size=strname_to_size)
    assert str_config.strname_to_size == strname_to_size


@pytest.mark.parametrize(
    'var, sz',
    [
        ['_A$', 1],
        ['AAA$', 1],
        ['9A$', 1],
        ['A()$', 1],
        ['()A$', 1],
        ['A$', 0],
        ['A$', 32767],
    ],
)
def test_fails_invalid_string_configs(var: str, sz: int):
    strname_to_size = {var: sz}
    with pytest.raises(ValidationError):
        configs.StringConfigs(strname_to_size=strname_to_size)
