import os
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from app.history import CalculationHistory


def make_calc(op="add", a=1, b=2, result=3, ts=None, ok=True, dur=5):
    ts = ts or datetime.now().isoformat()
    return {
        "operation": op,
        "operand_a": a,
        "operand_b": b,
        "result": result if ok else None,
        "expression": f"{a} {op} {b}",
        "error": None if ok else "boom",
        "timestamp": ts,
        "duration_ms": dur,
    }


def test_history_add_get_search_and_statistics(tmp_path):
    hist_file = tmp_path / "hist.csv"
    h = CalculationHistory(history_file=str(hist_file), auto_save=True, max_entries=100)

    # Add a few rows (mix success and failure, different ops and times)
    base = datetime.now() - timedelta(days=1)
    ids = []
    ids.append(h.add_calculation(make_calc("add", 1, 2, 3, ts=(base + timedelta(hours=1)).isoformat(), ok=True)))
    ids.append(h.add_calculation(make_calc("multiply", 3, 4, 12, ts=(base + timedelta(hours=2)).isoformat(), ok=True)))
    ids.append(h.add_calculation(make_calc("divide", 10, 0, None, ts=(base + timedelta(hours=3)).isoformat(), ok=False)))

    # get_calculation by id
    got = h.get_calculation(ids[1])
    assert got is not None and got["operation"] == "multiply"

    # recent vs all
    recent = h.get_recent_calculations(2)
    assert len(recent) == 2
    all_items = h.get_all_calculations()
    assert len(all_items) == 3

    # search by operation
    only_add = h.search_calculations(operation="add")
    assert len(only_add) == 1 and only_add[0]["operation"] == "add"

    # search by result range (should include 3 and 12)
    in_range = h.search_calculations(result_range=(2, 12))
    assert {r["result"] for r in in_range} >= {3, 12}

    # search by date range (narrow to last two)
    start = base + timedelta(hours=2)
    end = base + timedelta(hours=4)
    dr = h.search_calculations(date_range=(start, end))
    assert len(dr) == 2

    # success filter
    only_fail = h.search_calculations(success_only=False)
    assert len(only_fail) == 1 and only_fail[0]["success"] is False

    # statistics
    stats = h.get_statistics()
    assert stats["total_calculations"] == 3
    assert stats["successful_calculations"] == 2
    assert "operations_count" in stats and stats["operations_count"]["add"] == 1


def test_history_save_load_and_export(tmp_path):
    hist_file = tmp_path / "hist.csv"
    h = CalculationHistory(history_file=str(hist_file), auto_save=False, max_entries=10)

    h.add_calculation(make_calc("add", 1, 1, 2))
    h.add_calculation(make_calc("add", 2, 2, 4))

    # save and load round-trip
    h.save_history()
    assert hist_file.exists()

    h2 = CalculationHistory(history_file=str(hist_file), auto_save=False, max_entries=10)
    # It auto-loads on __init__ if file exists
    assert h2.get_count() == 2

    # export csv and json
    out_csv = tmp_path / "export.csv"
    out_json = tmp_path / "export.json"
    h2.export_history(str(out_csv), format="csv")
    h2.export_history(str(out_json), format="json")
    assert out_csv.exists() and out_json.exists()


def test_history_remove_trim_clear_and_compat(tmp_path):
    hist_file = tmp_path / "hist.csv"
    h = CalculationHistory(history_file=str(hist_file), auto_save=False, max_entries=3)

    # populate 4 items, max_entries=3 will trim on add
    for i in range(4):
        h.add_calculation(make_calc("add", i, i, i * 2, ts=(datetime.now() + timedelta(seconds=i)).isoformat()))
    assert h.get_count() == 3

    # remove_last then clear
    assert h.remove_last() is True
    h.clear_history()
    assert h.is_empty()

    # load_from_csv compatibility path (AutoSaveObserver schema)
    compat = tmp_path / "autosave.csv"
    pd.DataFrame([
        {
            "timestamp": datetime.now().isoformat(),
            "operation": "add",
            "operand_a": 1,
            "operand_b": 2,
            "result": 3,
            "expression": "1+2",
            "calculation_id": "abc",
        }
    ]).to_csv(compat, index=False)

    h.load_from_csv(str(compat))
    assert h.get_count() == 1
    # Operation is an object; compare the operation name string
    assert h.get_last_calculation().operation_name == "add"

    # trim_to_count keeps oldest-first
    h.trim_to_count(0)
    assert h.get_count() == 0
