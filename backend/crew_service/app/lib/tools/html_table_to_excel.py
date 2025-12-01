import base64
import logging
import os
from pathlib import Path

import xlsxwriter
from bs4 import BeautifulSoup
from crewai.tools import tool

from app.api.crud_client.models.artifact_type import ArtifactType
from app.lib.tools.utils.artifact import get_default_artifact_service
from app.lib.tools.utils.file_utils import cleanup_temp_file, TEMP_DIR


@tool("HTML Table to Excel Converter")
def html_table_to_excel_tool(
    html_str: str,
    file_name: str,
    crew_run_id: str,
):
    """
    AI Agent can use this tool to convert an HTML table string into an Excel (.xlsx) file
    with row/col spans preserved as merged cells.

    Args:
        html_str: The HTML table string to convert to Excel.
        file_name: The name of the Excel file to create.
        crew_run_id: Optional crew run identifier used to store the Excel file as an
            artifact in the CRUD service.
    """
    return html_table_to_excel(html_str, file_name, crew_run_id)


def html_table_to_excel(
    html_str: str,
    file_name: str,
    crew_run_id: str,
) -> str:
    """
    Core function: converts an HTML table string into an Excel (.xlsx) file
    with row/col spans preserved as merged cells.

    Returns:
        The original html_str (current behavior). If you prefer, you could
        change this to return `output_path` instead.
    """
    upload_file_name, output_path = _prepare_temp_output_path(
        file_name, "html_table_to_excel.xlsx", ".xlsx", crew_run_id
    )

    grid, merges = _parse_html_table_with_spans(html_str)

    try:
        workbook = None
        try:
            # Write with XlsxWriter and apply merges
            workbook = xlsxwriter.Workbook(output_path)
            worksheet = workbook.add_worksheet("Schedule")

            header_fmt = workbook.add_format(
                {"bold": True, "align": "center", "valign": "vcenter", "border": 1}
            )
            cell_fmt = workbook.add_format(
                {"text_wrap": True, "valign": "top", "border": 1}
            )

            # Collect all cells that will be merged
            merged_cells = set()
            for r1, c1, r2, c2, _ in merges:
                for r in range(r1, r2 + 1):
                    for c in range(c1, c2 + 1):
                        merged_cells.add((r, c))

            # Write non-merged cells
            for r, row in enumerate(grid):
                for c, val in enumerate(row):
                    if (r, c) in merged_cells:
                        continue
                    fmt = header_fmt if r == 0 else cell_fmt
                    worksheet.write(r, c, val, fmt)

            # Apply merges
            max_row = len(grid) - 1
            max_col = len(grid[0]) - 1 if grid else 0

            for r1, c1, r2, c2, val in merges:
                r2 = min(r2, max_row)
                c2 = min(c2, max_col)
                fmt = header_fmt if r1 == 0 else cell_fmt
                worksheet.merge_range(r1, c1, r2, c2, val, fmt)

            # Autosize columns
            if grid:
                for c in range(len(grid[0])):
                    max_len = max(
                        (len(str(grid[r][c])) for r in range(len(grid))), default=10
                    )
                    worksheet.set_column(c, c, min(60, max(12, max_len * 0.9)))
        finally:
            if workbook is not None:
                workbook.close()

        if crew_run_id:
            return _save_excel_artifact(
                output_path, crew_run_id, upload_file_name
            )

        return html_str
    finally:
        cleanup_temp_file(output_path)


def _parse_html_table_with_spans(html: str):
    """
    Returns: grid (list[list[str]]), merges (list[(r1, c1, r2, c2, value)])
    grid is a rectangular 0-based matrix of strings.
    merges contains inclusive cell coordinates for ranges to merge in Excel.
    """
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if table is None:
        raise ValueError("No <table> found in HTML.")

    grid = []
    merges = []
    col_count = 0
    occupied = {}  # (r, c) -> True

    rows = table.find_all("tr")
    for r_idx, tr in enumerate(rows):
        while len(grid) <= r_idx:
            grid.append([])
        row = grid[r_idx]

        # Extend current row to account for carried-over rowspans
        c_idx = 0
        while c_idx < col_count:
            if (r_idx, c_idx) in occupied:
                row.append("")  # covered cell
            else:
                row.append(None)  # free slot
            c_idx += 1

        cells = tr.find_all(["td", "th"])
        c_ptr = 0
        for cell in cells:
            # Move c_ptr to next free column (skip occupied)
            while True:
                if len(row) <= c_ptr:
                    row.append(None)
                if (r_idx, c_ptr) in occupied:
                    if row[c_ptr] is None:
                        row[c_ptr] = ""
                    c_ptr += 1
                    continue
                break

            text = cell.get_text(separator=" ", strip=True)
            rs = int(str(cell.get("rowspan", "1")))
            cs = int(str(cell.get("colspan", "1")))

            needed_cols = c_ptr + cs
            col_count = max(col_count, needed_cols)
            while len(row) < needed_cols:
                row.append(None)

            # Place top-left value
            row[c_ptr] = text

            # Record merge range if spanning
            if rs > 1 or cs > 1:
                r1, c1 = r_idx, c_ptr
                r2, c2 = r_idx + rs - 1, c_ptr + cs - 1
                merges.append((r1, c1, r2, c2, text))

                # Ensure enough rows for rowspan
                max_row_needed = r_idx + rs
                while len(grid) < max_row_needed:
                    grid.append([])

            # Mark covered cells in this row
            for dc in range(cs):
                if dc == 0:
                    continue
                if row[c_ptr + dc] is None:
                    row[c_ptr + dc] = ""

            # Mark occupied for future rows
            for dr in range(1, rs):
                rr = r_idx + dr
                while len(grid) <= rr:
                    grid.append([])
                future_row = grid[rr]
                while len(future_row) < col_count:
                    future_row.append(None)
                for dc in range(cs):
                    cc = c_ptr + dc
                    occupied[(rr, cc)] = True
                    if cc < len(future_row) and future_row[cc] is None:
                        future_row[cc] = ""

            c_ptr += cs

        # Clean up row
        for i in range(len(row)):
            if row[i] is None:
                row[i] = ""
        while len(row) < col_count:
            row.append("")

    # Final pass to normalize all rows
    for r in grid:
        for i in range(len(r)):
            if r[i] is None:
                r[i] = ""
        while len(r) < col_count:
            r.append("")

    return grid, merges


def _save_excel_artifact(
    output_path: str, crew_run_id: str, upload_file_name: str
) -> str:
    """Save generated Excel file as an artifact and return its S3 URL or error."""
    artifact_service = get_default_artifact_service()

    try:
        with open(output_path, "rb") as f:
            file_content_base64 = base64.b64encode(f.read()).decode("utf-8")
    except OSError as exc:
        error = f"Error: Unable to read generated Excel file: {exc}"
        logging.error("html_table_to_excel: %s", error)
        return error

    save_result = artifact_service.save_artifact(
        crew_run_id=crew_run_id,
        file_name=upload_file_name,
        file_content_base64=file_content_base64,
        artifact_type=ArtifactType.DOCUMENT,
    )
    if not save_result.is_success or not save_result.artifact:
        return save_result.error or "Error: Failed to save Excel artifact."

    s3_result = artifact_service.get_artifact_s3_url(
        artifact_id=save_result.artifact.id,
        crew_run_id=crew_run_id,
    )
    if not s3_result.is_success or not s3_result.url:
        return s3_result.error or "Error: Failed to obtain Excel artifact S3 URL."

    return s3_result.url


def _prepare_temp_output_path(
    file_name: str | None,
    default_name: str,
    suffix: str,
    crew_run_id: str | None,
) -> tuple[str, str]:
    """Return (upload_file_name, local_temp_path) inside .temp."""
    suffix = suffix if suffix.startswith(".") else f".{suffix}"
    base_name = (
        default_name if not file_name or not file_name.strip() else file_name.strip()
    )
    candidate = Path(base_name).name
    candidate_path = Path(candidate)
    if candidate_path.suffix.lower() != suffix.lower():
        candidate_path = candidate_path.with_suffix(suffix)

    upload_name = candidate_path.name
    local_name = upload_name if not crew_run_id else f"{crew_run_id}_{upload_name}"
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    return upload_name, str(TEMP_DIR / local_name)
