import pytest

from config import parse_stream_config


def test_defaults_used_when_no_args_and_no_config(tmp_path):
    config = parse_stream_config(["--config", str(tmp_path / "missing.json")])
    assert config.width == 640
    assert config.height == 480
    assert config.fps == 30


def test_json_config_used_when_present(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text('{"width": 1280, "height": 720, "fps": 25}')
    config = parse_stream_config(["--config", str(config_path)])
    assert config.width == 1280
    assert config.height == 720
    assert config.fps == 25


def test_cli_overrides_json(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text('{"width": 1280, "height": 720, "fps": 25}')
    config = parse_stream_config(
        ["--config", str(config_path), "--width", "1920", "--fps", "60"]
    )
    assert config.width == 1920
    assert config.height == 720
    assert config.fps == 60


@pytest.mark.parametrize(
    "args",
    [
        ["--width", "0"],
        ["--height", "0"],
        ["--fps", "0"],
        ["--width", "-1"],
        ["--height", "-1"],
        ["--fps", "-1"],
    ],
)
def test_invalid_values_raise(args):
    with pytest.raises(ValueError):
        parse_stream_config(args)
