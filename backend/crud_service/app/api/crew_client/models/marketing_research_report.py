from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="MarketingResearchReport")


@_attrs_define
class MarketingResearchReport:
    r"""Structured representation of the marketing‑research markdown report.

    The task’s `expected_output` asks for a markdown document that contains:

    • Executive summary
    • Competitive landscape
    • Emerging trends
    • Successful examples / references
    • Recommendations
    • References

    Each section is stored as a separate string so the workflow can either:
      – render the whole markdown (`report`) directly, or
      – access individual sections programmatically (e.g. for UI rendering, analytics, etc.).

    `metadata` can be used for generation timestamps, model version, or any other
    bookkeeping the system wants to keep.

        Example:
            {'competitive_landscape': 'Top 2‑3 competitors are ...', 'emerging_trends': 'Short‑form video, user‑generated
                content, ...', 'executive_summary': 'The market is shifting toward ...', 'recommendations': 'Post 3‑4 reels per
                week, leverage carousel posts ...', 'references': '1. https://example.com/competitor‑analysis\\n2.
                https://instagram.com/hashtag/…', 'successful_examples': '- @brand1 https://instagram.com/p/ABC123\\n- @brand2
                https://instagram.com/p/DEF456'}

        Attributes:
            executive_summary (str): High‑level overview of findings.
            competitive_landscape (str): Analysis of competitors identified.
            emerging_trends (str): Key trends tied to the campaign theme.
            successful_examples (str): Relevant Instagram examples with usernames & URLs.
            recommendations (str): Actionable advice for the upcoming campaign.
            references (str): Citations of web‑search & Instagram sources.
    """

    executive_summary: str
    competitive_landscape: str
    emerging_trends: str
    successful_examples: str
    recommendations: str
    references: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        executive_summary = self.executive_summary

        competitive_landscape = self.competitive_landscape

        emerging_trends = self.emerging_trends

        successful_examples = self.successful_examples

        recommendations = self.recommendations

        references = self.references

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "executive_summary": executive_summary,
                "competitive_landscape": competitive_landscape,
                "emerging_trends": emerging_trends,
                "successful_examples": successful_examples,
                "recommendations": recommendations,
                "references": references,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        executive_summary = d.pop("executive_summary")

        competitive_landscape = d.pop("competitive_landscape")

        emerging_trends = d.pop("emerging_trends")

        successful_examples = d.pop("successful_examples")

        recommendations = d.pop("recommendations")

        references = d.pop("references")

        marketing_research_report = cls(
            executive_summary=executive_summary,
            competitive_landscape=competitive_landscape,
            emerging_trends=emerging_trends,
            successful_examples=successful_examples,
            recommendations=recommendations,
            references=references,
        )

        marketing_research_report.additional_properties = d
        return marketing_research_report

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
