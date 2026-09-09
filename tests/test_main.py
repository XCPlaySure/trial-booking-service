import os
import runpy
import sys

import pytest


def test_main_module_entry(tmp_path):
    db = str(tmp_path / "main.db")
    sys.argv = ["trial_booking", "--db", db, "seed"]
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("trial_booking", run_name="__main__")
    assert exc.value.code == 0
    assert os.path.exists(db)