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
        "    InstanceConfig(email='a@x.com', password='p', course_url='https://c.org/c1', legal_name='User A'),\n"
        "    InstanceConfig(email='b@x.com', password='p', course_url='https://c.org/c2', legal_name='User B'),\n"
        "]\n",
        encoding="utf-8",
    )
    with patch("coursera_automation.main.run_instance") as mock_run:
        run(str(p))
        assert mock_run.call_count == 2


def test_instance_validation() -> None:
    """Verify InstanceConfig.validate() enforces real legal_name."""
    from coursera_automation.instances import InstanceConfig

    valid = InstanceConfig(email="a@x.com", password="p", course_url="https://c.org/c1", legal_name="Palak Chandel")
    valid.validate()
    assert valid.to_settings().legal_name == "Palak Chandel"

    with pytest.raises(ValueError, match="requires a valid 'legal_name'"):
        InstanceConfig(email="a@x.com", password="p", course_url="https://c.org/c1", legal_name="").validate()

    with pytest.raises(ValueError, match="requires a valid 'legal_name'"):
        InstanceConfig(email="a@x.com", password="p", course_url="https://c.org/c1", legal_name="Your Legal Name").validate()


def test_run_aborts_on_placeholder_legal_name(tmp_path: Path) -> None:
    """Verify run() aborts before execution if legal_name is placeholder."""
    from coursera_automation.main import run

    p = tmp_path / "bad_instance.py"
    p.write_text(
        "from coursera_automation.instances import InstanceConfig\n"
        "INSTANCES = [InstanceConfig(email='a@x.com', password='p', course_url='https://c.org/c1', legal_name='Your Legal Name')]\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="requires a valid 'legal_name'"):
        run(str(p))
