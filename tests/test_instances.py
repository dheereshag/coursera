"""Tests for multi-instance configuration loading from instances.py and json."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from coursera_automation.instances import load_instances


def test_load_instances_missing_raises(tmp_path: Path) -> None:
    """When config file is missing, raise ValueError."""
    missing = tmp_path / "nonexistent.py"
    with pytest.raises(ValueError, match="No valid instances"):
        load_instances(str(missing))


def test_load_instances_from_py(tmp_path: Path) -> None:
    """Correctly load instances from a Python configuration file."""
    p = tmp_path / "custom_instances.py"
    p.write_text(
        "from coursera_automation.instances import InstanceConfig\n"
        "INSTANCES = [\n"
        "    InstanceConfig(email='py1@cuchd.in', password='p1', course_url='https://coursera.org/c1', max_items=15),\n"
        "    InstanceConfig(email='py2@cuchd.in', password='p2', course_url='https://coursera.org/c2', headless=True),\n"
        "]\n",
        encoding="utf-8",
    )
    instances = load_instances(str(p))
    assert len(instances) == 2
    assert instances[0].email == "py1@cuchd.in"
    assert instances[0].max_items == 15
    assert instances[1].email == "py2@cuchd.in"
    assert instances[1].headless is True
    settings = instances[1].to_settings()
    assert settings.email == "py2@cuchd.in"
    assert settings.headless is True


def test_load_instances_from_json(tmp_path: Path) -> None:
    """Correctly load and parse multiple instances from JSON file."""
    p = tmp_path / "test_instances.json"
    data = [
        {
            "email": "test1@cuchd.in",
            "password": "pass1",
            "course_url": "https://coursera.org/c1",
            "headless": True,
            "max_items": 10,
        },
        {
            "email": "test2@cuchd.in",
            "password": "pass2",
            "course_url": "https://coursera.org/c2",
            "headless": False,
            "max_items": 20,
        },
    ]
    p.write_text(json.dumps(data), encoding="utf-8")
    instances = load_instances(str(p))
    assert len(instances) == 2
    assert instances[0].email == "test1@cuchd.in"
    assert instances[0].max_items == 10
    assert instances[1].email == "test2@cuchd.in"


def test_run_parallel(tmp_path: Path) -> None:
    """Verify run() executes instances concurrently via run_instance."""
    from coursera_automation.main import run

    p = tmp_path / "parallel.py"
    p.write_text(
        "from coursera_automation.instances import InstanceConfig\n"
        "INSTANCES = [\n"
        "    InstanceConfig(email='a@x.com', password='p', course_url='https://c.org/c1'),\n"
        "    InstanceConfig(email='b@x.com', password='p', course_url='https://c.org/c2'),\n"
        "]\n",
        encoding="utf-8",
    )
    with patch("coursera_automation.main.run_instance") as mock_run:
        run(str(p))
        assert mock_run.call_count == 2
