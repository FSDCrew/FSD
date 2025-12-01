from pathlib import Path


def resolve_output_path(
    file_name: str | None,
    default_name: str,
    required_suffix: str,
    base_dir: str = "./output",
) -> str:
    """Return an output path using the provided suffix inside base_dir when relative."""
    suffix = required_suffix if required_suffix.startswith(".") else f".{required_suffix}"
    candidate = Path(default_name if not file_name or not file_name.strip() else file_name.strip())

    if candidate.suffix.lower() != suffix.lower():
        candidate = candidate.with_suffix(suffix)

    if not candidate.is_absolute():
        candidate = Path(base_dir) / candidate

    return str(candidate)
