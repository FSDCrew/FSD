"""
Example script to generate Instagram copywriting for a single schedule item
and write the result to a markdown file.
"""

import json

from app.lib.tools.generate_copywriting import generate_copywriting_tool

def main() -> None:
    # Example schedule item – replace with real data as needed
    schedule_item = {
        "id": 1,
        "phase_name": "Phase 1",
        "week": 1,
        "date": "2023-01-01",
        "post_type": "image",
        "theme_concept": "Theme Concept",
        "objective": "Objective",
        "description": "Description",
    }

    # Generate the markdown copywriting using the existing tool
    markdown = generate_copywriting_tool._run(
        schedule_item_json=json.dumps(schedule_item)
    )

    # Write the output to a markdown file in the current directory
    output_path = "copywriting_output.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"✅ Copywriting markdown written to {output_path}")


if __name__ == "__main__":
    main()
