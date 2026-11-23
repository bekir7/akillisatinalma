from __future__ import annotations

from pathlib import Path

from .models import ComparisonResult, QuoteLine
from .normalize import normalize_dataframe
from .readers import list_quote_files, read_quote_file
from .report import format_console_report, write_excel_report
from .scoring import DEFAULT_WEIGHTS, compare_quotes


def run_comparison(
    input_dir: Path,
    output_path: Path,
    weights: dict[str, float] | None = None,
) -> tuple[list[QuoteLine], list[ComparisonResult], Path, str]:
    weights = weights or DEFAULT_WEIGHTS
    files = list_quote_files(input_dir)

    all_lines: list[QuoteLine] = []
    for path in files:
        df = read_quote_file(path)
        all_lines.extend(normalize_dataframe(df))

    if not all_lines:
        raise ValueError("Hiçbir teklif satırı okunamadı. Sütun eşlemesini kontrol edin.")

    results = compare_quotes(all_lines, weights=weights)
    report_path = write_excel_report(results, all_lines, output_path, weights)
    console_text = format_console_report(results, report_path)
    return all_lines, results, report_path, console_text
