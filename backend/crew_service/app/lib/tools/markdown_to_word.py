import base64
import logging
import os
import shutil
import textwrap
from pathlib import Path

import pypandoc
from crewai.tools import tool

from app.api.crud_client.models.artifact_type import ArtifactType
from app.lib.tools.utils.artifact import get_default_artifact_service
from app.lib.tools.utils.file_utils import cleanup_temp_file, TEMP_DIR


@tool("Markdown to Word Doc")
def markdown_to_word_doc(
    markdown: str,
    file_name: str,
    crew_run_id: str,
):
    """
    Convert Markdown string to a Word (.docx) using Pandoc, preserving Markdown features.

    - Uses GitHub-Flavored Markdown (GFM) with common extensions:
      tables, task lists, strikethrough, footnotes, $...$ math, smart quotes.
    """
    if not markdown or not markdown.strip():
        error = f"Markdown input is empty."
        logging.error("markdown_to_word_doc: ", error)
        return error

    _ensure_pandoc_env()
    upload_file_name, output_path = _prepare_temp_output_path(
        file_name, "markdown_to_word.docx", ".docx", crew_run_id
    )

    markdown = textwrap.dedent(markdown).lstrip("\ufeff").lstrip("\n")
    frmt = "gfm+smart+pipe_tables+strikeout+task_lists+tex_math_dollars+footnotes"

    try:
        pypandoc.convert_text(
            markdown,
            to="docx",
            format=frmt,
            outputfile=output_path,
        )

        if crew_run_id:
            return _save_word_doc_artifact(
                output_path, crew_run_id, upload_file_name
            )

        return markdown
    except Exception as e:
        error = f"Error converting Markdown to Word Doc: {e}"
        logging.error("markdown_to_word_doc: ", error)
        return error
    finally:
        cleanup_temp_file(output_path)


def _ensure_pandoc_env() -> None:
    """Ensure PYPANDOC_PANDOC points to a pandoc executable, downloading if needed."""
    if shutil.which("pandoc"):
        return
    downloaded = pypandoc.download_pandoc()
    if not downloaded:
        return
    p = Path(downloaded)
    pandoc_path = (
        p if p.is_file() else p / ("pandoc.exe" if os.name == "nt" else "pandoc")
    )
    os.environ["PYPANDOC_PANDOC"] = str(pandoc_path)


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


def _save_word_doc_artifact(
    output_path: str, crew_run_id: str, upload_file_name: str
) -> str:
    """Save generated docx as an artifact and return its S3 URL or error text."""
    artifact_service = get_default_artifact_service()

    try:
        with open(output_path, "rb") as f:
            file_content_base64 = base64.b64encode(f.read()).decode("utf-8")
    except OSError as exc:
        error = f"Error: Unable to read generated Word document: {exc}"
        logging.error("markdown_to_word_doc: %s", error)
        return error

    save_result = artifact_service.save_artifact(
        crew_run_id=crew_run_id,
        file_name=upload_file_name,
        file_content_base64=file_content_base64,
        artifact_type=ArtifactType.DOCUMENT,
    )

    if not save_result.is_success or not save_result.artifact:
        return save_result.error or "Error: Failed to save Word document artifact."

    s3_result = artifact_service.get_artifact_s3_url(
        artifact_id=save_result.artifact.id,
        crew_run_id=crew_run_id,
    )
    if not s3_result.is_success or not s3_result.url:
        return s3_result.error or "Error: Failed to obtain Word document S3 URL."

    return s3_result.url
