"""Helpers for building tiny official-format O*NET fixtures."""

from __future__ import annotations

import csv
from pathlib import Path

from app.recommendation.constants import (
    ESSENTIAL_SKILL_IDS,
    RIASEC_ELEMENT_IDS,
    TRANSFERABLE_SKILL_IDS,
    WORK_CONTEXT_IDS,
    WORK_STYLE_IDS,
)

SIA_IDS = tuple(f"1.B.3.x{i:02d}" for i in range(41))
KNOWLEDGE_IDS = tuple(f"2.C.x{i:02d}" for i in range(33))
ACTIVITY_IDS = tuple(f"4.A.x{i:02d}" for i in range(41))

COMPLETE_ZONE4 = "11-1011.00"
COMPLETE_ZONE2 = "11-1012.00"
INCOMPLETE = "11-1013.00"


def _write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def _rating(
    code: str,
    element_id: str,
    name: str,
    scale_id: str,
    value: str,
    *,
    not_relevant: str = "N",
    suppress: str = "N",
    category: str = "n/a",
) -> dict[str, str]:
    return {
        "O*NET-SOC Code": code,
        "Element ID": element_id,
        "Element Name": name,
        "Scale ID": scale_id,
        "Data Value": value,
        "N": "10",
        "Standard Error": "0.1",
        "Lower CI Bound": "1",
        "Upper CI Bound": "5",
        "Recommend Suppress": suppress,
        "Not Relevant": not_relevant,
        "Date": "08/2023",
        "Domain Source": "Test",
        "Category": category,
    }


def write_mini_onet(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "Read Me.txt").write_text(
        "O*NET 30.3 Database\nMay 2026 Release\n",
        encoding="utf-8",
    )

    _write_tsv(
        directory / "Occupation Data.txt",
        ["O*NET-SOC Code", "Title", "Description"],
        [
            {
                "O*NET-SOC Code": COMPLETE_ZONE4,
                "Title": "Complete Analyst",
                "Description": "A complete Zone 4 occupation.",
            },
            {
                "O*NET-SOC Code": COMPLETE_ZONE2,
                "Title": "Complete Helper",
                "Description": "A complete Zone 2 occupation.",
            },
            {
                "O*NET-SOC Code": INCOMPLETE,
                "Title": "Incomplete Occupation",
                "Description": "Missing knowledge ratings.",
            },
        ],
    )
    _write_tsv(
        directory / "Scales Reference.txt",
        ["Scale ID", "Scale Name", "Minimum", "Maximum"],
        [
            {"Scale ID": "OI", "Scale Name": "Occupational Interests", "Minimum": "1", "Maximum": "7"},
            {"Scale ID": "IM", "Scale Name": "Importance", "Minimum": "1", "Maximum": "5"},
            {"Scale ID": "WI", "Scale Name": "Work Styles Impact", "Minimum": "-3", "Maximum": "3"},
            {"Scale ID": "CX", "Scale Name": "Context", "Minimum": "1", "Maximum": "5"},
            {"Scale ID": "RL", "Scale Name": "Required Level Of Education", "Minimum": "0", "Maximum": "100"},
        ],
    )
    _write_tsv(
        directory / "Job Zones.txt",
        ["O*NET-SOC Code", "Job Zone", "Date", "Domain Source"],
        [
            {"O*NET-SOC Code": COMPLETE_ZONE4, "Job Zone": "4", "Date": "08/2023", "Domain Source": "Analyst"},
            {"O*NET-SOC Code": COMPLETE_ZONE2, "Job Zone": "2", "Date": "08/2023", "Domain Source": "Analyst"},
            {"O*NET-SOC Code": INCOMPLETE, "Job Zone": "4", "Date": "08/2023", "Domain Source": "Analyst"},
        ],
    )
    _write_tsv(
        directory / "Job Zone Reference.txt",
        ["Job Zone", "Name", "Experience", "Education", "Job Training", "Examples", "SVP Range"],
        [
            {
                "Job Zone": "2",
                "Name": "Job Zone 1-2",
                "Experience": "Little",
                "Education": "High school",
                "Job Training": "Short",
                "Examples": "Helpers",
                "SVP Range": "(Below 6.0)",
            },
            {
                "Job Zone": "4",
                "Name": "Job Zone Four",
                "Experience": "Considerable",
                "Education": "Bachelor's",
                "Job Training": "Several years",
                "Examples": "Analysts",
                "SVP Range": "(7.0 to < 8.0)",
            },
        ],
    )
    _write_tsv(
        directory / "Education Categories.txt",
        ["Element ID", "Element Name", "Scale ID", "Category", "Category Description"],
        [
            {
                "Element ID": "2.D.1",
                "Element Name": "Required Level of Education",
                "Scale ID": "RL",
                "Category": "6",
                "Category Description": "Bachelor's Degree",
            }
        ],
    )

    simple_rating_fields = [
        "O*NET-SOC Code",
        "Element ID",
        "Element Name",
        "Scale ID",
        "Data Value",
        "Date",
        "Domain Source",
    ]
    riasec_rows = []
    for code in (COMPLETE_ZONE4, COMPLETE_ZONE2, INCOMPLETE):
        for i, element_id in enumerate(RIASEC_ELEMENT_IDS, start=1):
            riasec_rows.append(
                {
                    "O*NET-SOC Code": code,
                    "Element ID": element_id,
                    "Element Name": element_id,
                    "Scale ID": "OI",
                    "Data Value": str(i),
                    "Date": "08/2023",
                    "Domain Source": "Test",
                }
            )
    _write_tsv(directory / "Career Interest Types.txt", simple_rating_fields, riasec_rows)

    styles_rows = []
    for code in (COMPLETE_ZONE4, COMPLETE_ZONE2, INCOMPLETE):
        for element_id in WORK_STYLE_IDS:
            styles_rows.append(
                {
                    "O*NET-SOC Code": code,
                    "Element ID": element_id,
                    "Element Name": element_id,
                    "Scale ID": "WI",
                    "Data Value": "0",
                    "Date": "08/2023",
                    "Domain Source": "Test",
                }
            )
    _write_tsv(directory / "Work Styles.txt", simple_rating_fields, styles_rows)

    flagged_fields = [
        "O*NET-SOC Code",
        "Element ID",
        "Element Name",
        "Scale ID",
        "Data Value",
        "N",
        "Standard Error",
        "Lower CI Bound",
        "Upper CI Bound",
        "Recommend Suppress",
        "Not Relevant",
        "Date",
        "Domain Source",
        "Category",
    ]

    def write_domain(filename: str, scale_id: str, ids: tuple[str, ...], codes: tuple[str, ...]) -> None:
        rows = []
        for code in codes:
            for element_id in ids:
                not_relevant = "N"
                suppress = "N"
                value = "4"
                if (
                    filename == "Knowledge.txt"
                    and code == COMPLETE_ZONE4
                    and element_id == ids[0]
                ):
                    not_relevant = "Y"
                    value = "5"
                if (
                    filename == "Essential Skills.txt"
                    and code == COMPLETE_ZONE4
                    and element_id == ids[0]
                ):
                    suppress = "Y"
                    value = "5"
                rows.append(
                    _rating(
                        code,
                        element_id,
                        element_id,
                        scale_id,
                        value,
                        not_relevant=not_relevant,
                        suppress=suppress,
                    )
                )
        _write_tsv(directory / filename, flagged_fields, rows)

    write_domain("Specific Interest Areas.txt", "OI", SIA_IDS, (COMPLETE_ZONE4, COMPLETE_ZONE2, INCOMPLETE))
    write_domain("Knowledge.txt", "IM", KNOWLEDGE_IDS, (COMPLETE_ZONE4, COMPLETE_ZONE2))
    write_domain("Essential Skills.txt", "IM", ESSENTIAL_SKILL_IDS, (COMPLETE_ZONE4, COMPLETE_ZONE2, INCOMPLETE))
    write_domain(
        "Transferable Skills.txt",
        "IM",
        TRANSFERABLE_SKILL_IDS,
        (COMPLETE_ZONE4, COMPLETE_ZONE2, INCOMPLETE),
    )
    write_domain("Work Activities.txt", "IM", ACTIVITY_IDS, (COMPLETE_ZONE4, COMPLETE_ZONE2, INCOMPLETE))
    write_domain("Work Context.txt", "CX", WORK_CONTEXT_IDS, (COMPLETE_ZONE4, COMPLETE_ZONE2, INCOMPLETE))

    education_rows = []
    for code in (COMPLETE_ZONE4, COMPLETE_ZONE2):
        education_rows.append(
            _rating(
                code,
                "2.D.1",
                "Required Level of Education",
                "RL",
                "80",
                category="6",
            )
        )
    _write_tsv(directory / "Education.txt", flagged_fields, education_rows)
    return directory
