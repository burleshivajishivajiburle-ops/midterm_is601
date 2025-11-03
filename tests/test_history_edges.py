import os
from datetime import datetime, timedelta
from pathlib import Path
import pytest

from app.history import CalculationHistory
from app.exceptions import FileOperationError


def make_calc(op="add", a=1, b=2, result=3, ts=None, ok=True, dur=1):
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


def test_history_load_nonexistent_and_export_filters_and_unsupported(tmp_path):
    h = CalculationHistory(history_file=str(tmp_path / "hist.csv"), auto_save=False, max_entries=5)

    # load_history on nonexistent file should raise FileOperationError
    with pytest.raises(FileOperationError):
        h.load_history(str(tmp_path / "nope.csv"))

    # add some and export json
    h.add_calculation(make_calc("add", 1, 1, 2))
    h.add_calculation(make_calc("multiply", 2, 3, 6))
    out_json = tmp_path / "out.json"
    h.export_history(str(out_json), format="json", filters={"operation": "add", "success_only": True})
    assert out_json.exists() and out_json.read_text().strip().startswith("[")

    # export excel (requires openpyxl)
    out_xlsx = tmp_path / "out.xlsx"
    h.export_history(str(out_xlsx), format="excel")
    assert out_xlsx.exists() and out_xlsx.stat().st_size > 0

    # unsupported format surfaces as FileOperationError
    with pytest.raises(FileOperationError):
        h.export_history(str(tmp_path / "x.bin"), format="binary")


def test_history_filters_and_edge_operations(tmp_path):
    h = CalculationHistory(history_file=str(tmp_path / "hist.csv"), auto_save=False, max_entries=10)

    base = datetime.now() - timedelta(days=2)
    h.add_calculation(make_calc("add", 1, 1, 2, ts=(base + timedelta(hours=1)).isoformat()))
    h.add_calculation(make_calc("add", 2, 2, 4, ts=(base + timedelta(hours=2)).isoformat()))
    h.add_calculation(make_calc("divide", 1, 0, None, ts=(base + timedelta(hours=3)).isoformat(), ok=False))

    # result_range boundary inclusive
    rng = h.search_calculations(result_range=(2, 4))
    assert {r["result"] for r in rng} == {2, 4}

    # date_range boundary inclusive
    start = base + timedelta(hours=1)
    end = base + timedelta(hours=2)
    dr = h.search_calculations(date_range=(start, end))
    assert len(dr) == 2

    # success_only True
    succ = h.search_calculations(success_only=True)
    assert all(r["success"] for r in succ)

    # remove when empty
    h.clear_history()
    assert h.remove_last() is False

    # get_operation_history helper and remove_calculation non-existent
    h.add_calculation(make_calc("add", 5, 5, 10))
    assert h.get_operation_history("add", limit=1)
    assert h.remove_calculation("does-not-exist") is False

    # load empty file should not crash and produce empty DataFrame
    empty = tmp_path / "empty.csv"
    empty.write_text("")
    h2 = CalculationHistory(history_file=str(empty), auto_save=False)
    # constructor should load empty gracefully
    assert h2.is_empty()

    # save error by monkeypatching to_csv
    import pandas as pd
    real_to_csv = pd.DataFrame.to_csv

    def bad_to_csv(self, *args, **kwargs):
        raise OSError("deny")

    try:
        pd.DataFrame.to_csv = bad_to_csv
        with pytest.raises(FileOperationError):
            h.save_history(str(tmp_path / "cannot" / "h.csv"))
    finally:
        pd.DataFrame.to_csv = real_to_csv
