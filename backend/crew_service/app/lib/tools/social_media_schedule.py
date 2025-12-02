from html import escape
import json
from typing import List, Type
import datetime

from crewai import LLM
from pydantic import BaseModel, ConfigDict, Field

from app.lib.tools.html_table_to_excel import html_table_to_excel
from app.models.models import CampaignWeekPlan, ContentStrategy, ScheduleItem, SocialMediaSchedule, StrategyPhase
from app.lib.tools.dates import _parse_date, calculate_num_weeks_impl
from crewai.tools import BaseTool

from app.lib.tools.utils.validate import validate_custom_type
from app.services.flow.llm_registry import general_llm


class GenerateSocialMediaScheduleInput(BaseModel):
    content_strategy_json: str = Field(
        ...,
        description="ContentStrategy object in JSON format containing the phases and their details"
    )
    start_date: str = Field(
        ...,
        description="The start date of the campaign in various formats: "
        "ISO format ('2024-01-01' or '2024-01-01T00:00:00Z'), "
        "DD-MMM-YYYY ('01-Nov-2024'), DD/MM/YYYY ('01/11/2024'), "
        "or YYYY-MM-DD ('2024-11-01')"
    )
    end_date: str = Field(
        ...,
        description="The end date of the campaign in the same formats as start_date"
    )
    crew_run_id: str = Field(
        ...,
        description="The crew run ID of the campaign"
    )

class GenerateSocialMediaSchedule(BaseTool):
    name: str = "generate_social_media_schedule"
    description: str = (
        "Generates a complete weekly social media posting schedule covering the entire "
        "period from <START_DATE> to <END_DATE>, based strictly on the <CONTENT_STRATEGY>. "
        "Returns a SocialMediaSchedule object with html_table, items (list of ScheduleItem objects)."
    )
    args_schema: Type[BaseModel] = GenerateSocialMediaScheduleInput
    
    def _run(
        self,
        start_date: str,
        end_date: str,
        content_strategy_json: str,
        crew_run_id: str,
    ) -> SocialMediaSchedule:
        """
        AI Agent can use this tool to generate SocialMediaSchedule
        
        1. Convert ContentStrategy.phases to CampaignWeekPlan objects
        2. Generate a list of ScheduleItem objects for each CampaignWeekPlan
        3. Convert the list of ScheduleItem objects to an HTML table
        4. Convert the HTML table to an Excel file
        5. Return the SocialMediaSchedule object
        """
        content_strategy = validate_custom_type(
            "ContentStrategy",
            content_strategy_json,
            strict=True,
        )


        campaign_week_plans = generate_campaign_week_plans(start_date, end_date, content_strategy.phases)
        campaign_schedule_items = generate_schedule_items(campaign_week_plans, content_strategy)
        html_table_str = schedule_items_to_html_table(campaign_schedule_items)
        _ = html_table_to_excel(html_table_str, "social_media_schedule.xlsx", crew_run_id)
        return SocialMediaSchedule(
            items=campaign_schedule_items,
        )


def generate_campaign_week_plans(
    start_date: str,
    end_date: str,
    phases: List[StrategyPhase],
) -> List[CampaignWeekPlan]:
    """
    Generate the campaign week plans by mapping phases to calendar weeks.

    Args:
        start_date: The start date of the campaign in various formats.
        end_date: The end date of the campaign in the same formats as start_date.
        phases: List of StrategyPhase objects.

    Returns:
        A list of CampaignWeekPlan objects, one per week.
    """
    # Parse and validate dates
    start_date_obj = _parse_date(start_date).date()
    end_date_obj = _parse_date(end_date).date()

    if start_date_obj > end_date_obj:
        raise ValueError("start_date must be on or before end_date")

    if not phases:
        raise ValueError("At least one phase is required")

    # Derive total_weeks from the date range
    total_weeks = calculate_num_weeks_impl(start_date, end_date)
    if total_weeks <= 0:
        raise ValueError(
            "total_weeks must be positive; check that start_date is on or before end_date"
        )

    # Allocate weeks per phase
    phase_weeks = allocate_phase_weeks(phases, total_weeks)

    # Build week plans
    week_plans: List[CampaignWeekPlan] = []
    current_start = start_date_obj
    week_number = 1

    for phase, weeks_for_phase in zip(phases, phase_weeks):
        for _ in range(weeks_for_phase):
            if current_start > end_date_obj:
                break

            week_start = current_start
            week_end = min(
                week_start + datetime.timedelta(days=6),
                end_date_obj,
            )

            wp = CampaignWeekPlan(
                week_number=week_number,
                phase_name=phase.name,
                week_start=week_start,
                week_end=week_end,
                phase_themes=list(phase.themes),
                phase_objectives=list(phase.objectives),
                posting_cadence=dict(phase.posting_cadence),
                recommended_content_types=list(phase.recommended_content_types),
                messaging_guidelines=(
                    list(phase.messaging_guidelines)
                    if phase.messaging_guidelines is not None
                    else None
                ),
            )
            week_plans.append(wp)

            week_number += 1
            current_start = week_end + datetime.timedelta(days=1)

        if current_start > end_date_obj:
            break

    return week_plans


def allocate_phase_weeks(
    phases: List[StrategyPhase],
    total_weeks: int,
) -> List[int]:
    """
    Use the phase.duration_in_weeks as the primary signal.
    If the sum matches total_weeks, return them directly.
    Otherwise, scale proportionally and adjust in a single pass
    to get as close as possible to total_weeks.
    """
    if total_weeks <= 0:
        raise ValueError("total_weeks must be positive")
    if not phases:
        raise ValueError("At least one phase is required")

    raw_durations = [max(1, p.duration_in_weeks) for p in phases]
    total_phase_weeks = sum(raw_durations)

    if total_phase_weeks <= 0:
        raise ValueError("Sum of phase durations must be positive")

    # Perfect match: just use the configured durations
    if total_phase_weeks == total_weeks:
        return raw_durations

    # Otherwise, scale and adjust
    scaled = [d * total_weeks / total_phase_weeks for d in raw_durations]
    allocated = [max(1, int(x)) for x in scaled]
    current_sum = sum(allocated)

    if current_sum < total_weeks:
        extra = total_weeks - current_sum

        indices = sorted(
            range(len(scaled)),
            key=lambda i: scaled[i] - int(scaled[i]),
            reverse=True,
        )

        for i in indices:
            if extra == 0:
                break
            allocated[i] += 1
            extra -= 1

    elif current_sum > total_weeks:
        to_remove = current_sum - total_weeks

        indices = sorted(
            range(len(scaled)),
            key=lambda i: scaled[i] - int(scaled[i]),
        )

        for i in indices:
            if to_remove == 0:
                break
            if allocated[i] > 1:
                allocated[i] -= 1
                to_remove -= 1

    return allocated


def generate_schedule_items(
    campaign_week_plans: List[CampaignWeekPlan],
    content_strategy: ContentStrategy,
) -> list[ScheduleItem]:
    """
    Generate the schedule items for each campaign week plan.
    Auto-assigns sequential integer IDs starting from 1 if not provided.
    """
    campaign_schedule_items = []
    
    class ScheduleItemsResponse(BaseModel):
        schedule_items: List[ScheduleItem] = Field(
            ...,
            description="List of ScheduleItem objects representing scheduled Instagram content"
        )
        model_config = ConfigDict(
            extra="forbid",
            json_schema_extra={
                "additionalProperties": False
            }
        )
    
    llm = LLM(
        model=general_llm.model,
        response_format=ScheduleItemsResponse,
        temperature=0.7,
        seed=42,
    )
    
    for campaign_week_plan in campaign_week_plans:
        prompt = (
            "<your_task>\n"
            "Generate a list of ScheduleItem objects for the campaign week plan:\n"
            "<CAMPAIGN_WEEK_PLAN>\n"
            f"{campaign_week_plan.model_dump_json(indent=2)}\n"
            "</CAMPAIGN_WEEK_PLAN>\n"
            "You MUST ground the schedule items with the global settings:\n"
            "<GLOBAL_SETTINGS>\n"
            f"{json.dumps(content_strategy.global_settings, indent=2)}\n"
            "</GLOBAL_SETTINGS>\n"
            "Respond ONLY with JSON format.\n"
            "{\n"
            '    "schedule_items": [ScheduleItem objects]\n'
            "}\n"
            "</your_task>\n"
        )
        response = llm.call(prompt)
        if isinstance(response, str):
            parsed = ScheduleItemsResponse.model_validate_json(response)
        elif isinstance(response, dict):
            parsed = ScheduleItemsResponse.model_validate(response)
        else:
            parsed = response
        campaign_schedule_items.extend(parsed.schedule_items)
    
    # Auto-assign sequential IDs starting from 1 if not provided or if duplicates exist
    existing_ids = set()
    next_id = 1
    updated_items = []
    
    for item in campaign_schedule_items:
        if not hasattr(item, 'id') or item.id in existing_ids or item.id < 1:
            # Create a new item with the assigned id
            item_dict = item.model_dump()
            item_dict['id'] = next_id
            updated_items.append(ScheduleItem(**item_dict))
            existing_ids.add(next_id)
            next_id += 1
        else:
            updated_items.append(item)
            existing_ids.add(item.id)
            if item.id >= next_id:
                next_id = item.id + 1
        
    return updated_items


def schedule_items_to_html_table(items: List[ScheduleItem]) -> str:
    """
    Convert a list of ScheduleItem objects into an HTML table with rowspans
    for Phase (across all its weeks) and Week (within each phase).
    """
    # Empty table fallback
    if not items:
        return (
            '<table border="1" cellpadding="6" cellspacing="0">'
            "<thead>"
            "<tr>"
            "<th>Phase</th>"
            "<th>Week</th>"
            "<th>Post Type</th>"
            "<th>Date</th>"
            "<th>Theme/Concept</th>"
            "<th>Objective</th>"
            "<th>Description</th>"
            "</tr>"
            "</thead>"
            "<tbody></tbody>"
            "</table>"
        )

    # Sort items by week, date, post_type to establish chronological order
    items_sorted = sorted(
        items,
        key=lambda i: (i.week, i.date, i.post_type)
    )

    # Group by phase, then by week within phase
    phase_weeks: dict[str, dict[int, List[ScheduleItem]]] = {}
    phase_order: List[str] = []

    for item in items_sorted:
        phase_name = item.phase_name or ""
        week_number = item.week

        if phase_name not in phase_weeks:
            phase_weeks[phase_name] = {}
            phase_order.append(phase_name)

        weeks_dict = phase_weeks[phase_name]
        if week_number not in weeks_dict:
            weeks_dict[week_number] = []
        weeks_dict[week_number].append(item)

    html_parts: List[str] = []
    html_parts.append('<table border="1" cellpadding="6" cellspacing="0">')
    html_parts.append("<thead>")
    html_parts.append(
        "<tr>"
        "<th>Phase</th>"
        "<th>Week</th>"
        "<th>Post Type</th>"
        "<th>Date</th>"
        "<th>Theme/Concept</th>"
        "<th>Objective</th>"
        "<th>Description</th>"
        "</tr>"
    )
    html_parts.append("</thead>")
    html_parts.append("<tbody>")

    # Render rows: outer loop = phases (in order of first appearance),
    # inner loop = weeks within each phase, then items within each week.
    for phase_name in phase_order:
        weeks_dict = phase_weeks[phase_name]

        # Total number of rows this phase spans
        phase_rowspan = sum(len(week_items) for week_items in weeks_dict.values())
        phase_cell_written = False

        for week_number in sorted(weeks_dict.keys()):
            week_items = weeks_dict[week_number]
            week_rowspan = len(week_items)

            for idx, item in enumerate(week_items):
                html_parts.append("<tr>")

                # Phase cell: once per phase, spanning all rows in that phase
                if not phase_cell_written:
                    html_parts.append(
                        f'<td rowspan="{phase_rowspan}">{escape(str(phase_name))}</td>'
                    )
                    phase_cell_written = True

                # Week cell: once per week, spanning all rows in that week (within this phase)
                if idx == 0:
                    html_parts.append(
                        f'<td rowspan="{week_rowspan}">{escape(str(week_number))}</td>'
                    )

                html_parts.append(f"<td>{escape(item.post_type)}</td>")
                html_parts.append(f"<td>{escape(item.date.isoformat())}</td>")
                html_parts.append(f"<td>{escape(item.theme_concept)}</td>")
                html_parts.append(f"<td>{escape(item.objective)}</td>")
                html_parts.append(f"<td>{escape(item.description)}</td>")

                html_parts.append("</tr>")

    html_parts.append("</tbody>")
    html_parts.append("</table>")

    return "".join(html_parts)


generate_social_media_schedule_tool = GenerateSocialMediaSchedule()
