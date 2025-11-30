import logging
from pathlib import Path
import os, shutil
import textwrap
import pypandoc
from crewai.tools import tool
from typing import Optional, Sequence

from app.lib.tools.output_paths import resolve_output_path

def _ensure_pandoc_env() -> None:
    """Ensure PYPANDOC_PANDOC points to a pandoc executable, downloading if needed."""
    if shutil.which("pandoc"):
        return
    downloaded = pypandoc.download_pandoc()
    if not downloaded:
        return
    p = Path(downloaded)
    pandoc_path = p if p.is_file() else p / ("pandoc.exe" if os.name == "nt" else "pandoc")
    os.environ["PYPANDOC_PANDOC"] = str(pandoc_path)

def _safe_mkdirs(path: str) -> None:
    d = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(d, exist_ok=True)

@tool("Markdown to Word Doc")
def markdown_to_word_doc(
    markdown: str,
    file_name: str | None = None,
):
    """
    Convert Markdown string to a Word (.docx) using Pandoc, preserving Markdown features.

    - Uses GitHub-Flavored Markdown (GFM) with common extensions:
      tables, task lists, strikethrough, footnotes, $...$ math, smart quotes.
    - Optionally map styles via a Word template (reference_docx).
    - Optionally set resource_path so relative images are embedded properly.
    """
    output_path = resolve_output_path(file_name, "markdown_to_word.docx", ".docx")
    if not markdown or not markdown.strip():
        error = f"Markdown input is empty."
        logging.error("markdown_to_word_doc: ", error)
        return error
    
    if not output_path.lower().endswith(".docx"):
        error = f"output_path must end with .docx (Pandoc targets .docx, not legacy .doc): {output_path}"
        logging.error("markdown_to_word_doc: ", error)
        return error

    _ensure_pandoc_env()
    _safe_mkdirs(output_path)
    
    markdown = textwrap.dedent(markdown).lstrip("\ufeff").lstrip("\n")
    frmt = "gfm+smart+pipe_tables+strikeout+task_lists+tex_math_dollars+footnotes"

    try:
        pypandoc.convert_text(
            markdown,
            to="docx",
            format=frmt,
            outputfile=output_path,
        )
        return markdown
    except Exception as e:
        error = f"Error converting Markdown to Word Doc: {e}"
        logging.error("markdown_to_word_doc: ", error)
        return error 
