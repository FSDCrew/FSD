from crewai.tools import tool
from bs4 import BeautifulSoup
import xlsxwriter
import os

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

    # Build a grid honoring row/col spans
    grid = []
    merges = []
    col_count = 0
    occupied = {}  # (r, c) -> True    tracks cells covered by prior rowspans

    rows = table.find_all("tr")
    for r_idx, tr in enumerate(rows):
        # Ensure grid has this row
        while len(grid) <= r_idx:
            grid.append([])
        row = grid[r_idx]

        # Extend current row to account for carried-over rowspans
        c_idx = 0
        while c_idx < col_count:
            if (r_idx, c_idx) in occupied:
                # Placeholder for a covered cell (will be filled with "")
                row.append("")
            else:
                row.append(None)  # free slot to fill
            c_idx += 1

        cells = tr.find_all(["td", "th"])
        c_ptr = 0
        for cell in cells:
            # Move c_ptr to next free column (skip occupied)
            while True:
                if len(row) <= c_ptr:
                    row.append(None)
                # Skip columns occupied by a rowspan from above
                if (r_idx, c_ptr) in occupied:
                    if row[c_ptr] == None:
                        row[c_ptr] = ""
                    c_ptr += 1
                    continue
                break

            text = cell.get_text(separator=" ", strip=True)
            rs = int(str(cell.get("rowspan", "1")))
            cs = int(str(cell.get("colspan", "1")))


            # Make sure grid rows have enough columns
            needed_cols = c_ptr + cs
            col_count = max(col_count, needed_cols)
            while len(row) < needed_cols:
                row.append(None)

            # Place the top-left value
            row[c_ptr] = text

            # Mark merge if span>1
            if rs > 1 or cs > 1:
                r1, c1 = r_idx, c_ptr
                r2, c2 = r_idx + rs - 1, c_ptr + cs - 1
                merges.append((r1, c1, r2, c2, text))

                # Ensure grid has enough rows to accommodate this rowspan
                max_row_needed = r_idx + rs
                while len(grid) < max_row_needed:
                    grid.append([])

            # Mark covered cells (rightwards in this row)
            for dc in range(cs):
                if dc == 0:
                    continue
                if row[c_ptr + dc] is None:
                    row[c_ptr + dc] = ""
            # Mark occupied for future rows (downwards)
            for dr in range(1, rs):
                rr = r_idx + dr
                # Ensure this row exists in grid and is properly initialized
                while len(grid) <= rr:
                    grid.append([])
                future_row = grid[rr]
                # Ensure future row has enough columns and mark occupied cells
                while len(future_row) < col_count:
                    future_row.append(None)
                for dc in range(cs):
                    cc = c_ptr + dc
                    occupied[(rr, cc)] = True
                    # Mark the occupied cell as empty string in the grid
                    if cc < len(future_row):
                        future_row[cc] = ""

            c_ptr += cs

        # Replace remaining None with "" and pad to col_count
        for i in range(len(row)):
            if row[i] is None:
                row[i] = ""
        while len(row) < col_count:
            row.append("")

    # Ensure all rows have equal columns and are properly initialized
    # This handles cases where rowspans extended beyond actual HTML rows
    for r_idx, r in enumerate(grid):
        # Initialize any cells that are None
        for c_idx in range(len(r)):
            if r[c_idx] is None:
                r[c_idx] = ""
        # Pad to col_count
        while len(r) < col_count:
            r.append("")
    
    return grid, merges

@tool("HTML Table to Excel Converter")
def html_table_to_excel_tool(
    html_str: str,
    # output_path: str | None = None
) -> str:
    """
    Converts an HTML table string into an Excel (.xlsx) file with row/col spans preserved as merged cells.
    Only the first <table> is processed.
    """
    # output_path = output_path or "./output/html_table_to_excel.xlsx"
    output_path = "./output/html_table_to_excel.xlsx" # TODO: remove this
    try:
        grid, merges = _parse_html_table_with_spans(html_str)

        # Ensure output dir exists
        outdir = os.path.dirname(output_path) or "."
        os.makedirs(outdir, exist_ok=True)

        # Write with XlsxWriter and apply merges
        workbook = xlsxwriter.Workbook(output_path)
        worksheet = workbook.add_worksheet("Schedule")

        # Optional formatting
        header_fmt = workbook.add_format({"bold": True, "align": "center", "valign": "vcenter", "border": 1})
        cell_fmt = workbook.add_format({"text_wrap": True, "valign": "top", "border": 1})

        # Build a set of ALL cells that are part of merge ranges (including top-left)
        # These will be handled by merge_range, not written individually
        merged_cells = set()
        for r1, c1, r2, c2, val in merges:
            for r in range(r1, r2 + 1):
                for c in range(c1, c2 + 1):
                    merged_cells.add((r, c))

        # Write cells (skip ALL cells that are part of merge ranges)
        # merge_range will handle writing merged cells
        for r, row in enumerate(grid):
            for c, val in enumerate(row):
                if (r, c) in merged_cells:
                    continue  # Skip all cells that will be merged
                # Heuristic: first row as header if <th> used in HTML; if not sure, just use cell_fmt for all
                fmt = cell_fmt
                if r == 0:  # treat first row as header for simplicity
                    fmt = header_fmt
                worksheet.write(r, c, val, fmt)

        # Apply merges (XlsxWriter uses inclusive ranges, 0-based)
        # merge_range will write the value and format to the merged range
        max_row = len(grid) - 1
        max_col = len(grid[0]) - 1 if grid else 0
        for r1, c1, r2, c2, val in merges:
            # Clamp merge range to actual grid bounds (safety check)
            r2 = min(r2, max_row)
            c2 = min(c2, max_col)
            # Pick header vs cell format based on r1 (top-left row)
            fmt = header_fmt if r1 == 0 else cell_fmt
            worksheet.merge_range(r1, c1, r2, c2, val, fmt)

        # Autosize columns a bit
        for c in range(len(grid[0]) if grid else 0):
            # simple width guess
            max_len = max((len(str(grid[r][c])) for r in range(len(grid))), default=10)
            worksheet.set_column(c, c, min(60, max(12, max_len * 0.9)))

        workbook.close()
        return html_str
    except Exception as e:
        return f"Error converting HTML Table to Excel: {e}"
