"""Occupation read queries. No recommendation scoring."""

from __future__ import annotations

from math import ceil

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import (
    EducationCategory,
    JobZoneDefinition,
    Occupation,
    OccupationFeature,
    OnetSnapshot,
    SystemConfig,
)
from app.recommendation.constants import FEATURE_VERSION
from app.schemas.api import (
    OccupationActivityItem,
    OccupationDetail,
    OccupationEducationItem,
    OccupationFeatureItem,
    OccupationListResponse,
    OccupationSummary,
)


def active_feature_version(session: Session) -> str:
    row = session.get(SystemConfig, "active_feature_version")
    if row is None:
        return FEATURE_VERSION
    value = (row.value_json or {}).get("value")
    return str(value or FEATURE_VERSION)


def get_active_snapshot(session: Session) -> OnetSnapshot | None:
    version = active_feature_version(session)
    return session.scalar(select(OnetSnapshot).where(OnetSnapshot.feature_version == version))


def list_occupations(
    session: Session,
    *,
    page: int,
    page_size: int,
    recommendable: bool | None = None,
) -> OccupationListResponse:
    snapshot = get_active_snapshot(session)
    if snapshot is None:
        return OccupationListResponse(items=[], page=page, page_size=page_size, total=0, total_pages=0)

    filters = [Occupation.snapshot_id == snapshot.id]
    if recommendable is not None:
        filters.append(Occupation.recommendable.is_(recommendable))

    total = int(session.scalar(select(func.count()).select_from(Occupation).where(*filters)) or 0)
    total_pages = ceil(total / page_size) if total else 0
    offset = (page - 1) * page_size
    rows = session.scalars(
        select(Occupation)
        .where(*filters)
        .order_by(Occupation.onetsoc_code)
        .offset(offset)
        .limit(page_size)
    ).all()
    items = [OccupationSummary.model_validate(row) for row in rows]
    return OccupationListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


def get_occupation(session: Session, soc_code: str) -> OccupationDetail:
    snapshot = get_active_snapshot(session)
    if snapshot is None:
        raise NotFoundError(f"Occupation {soc_code} was not found")
    occupation = session.scalar(
        select(Occupation).where(
            Occupation.snapshot_id == snapshot.id,
            Occupation.onetsoc_code == soc_code,
        )
    )
    if occupation is None:
        raise NotFoundError(f"Occupation {soc_code} was not found")
    zone_name = None
    zone_education = None
    zone_experience = None
    if occupation.job_zone is not None:
        zone = session.scalar(
            select(JobZoneDefinition).where(
                JobZoneDefinition.snapshot_id == snapshot.id,
                JobZoneDefinition.job_zone == occupation.job_zone,
            )
        )
        if zone is not None:
            zone_name = zone.name
            zone_education = zone.education
            zone_experience = zone.experience
    feature_rows = session.scalars(
        select(OccupationFeature)
        .where(
            OccupationFeature.occupation_id == occupation.id,
            OccupationFeature.domain.in_(("education", "work_activities", "riasec")),
        )
        .order_by(OccupationFeature.domain, OccupationFeature.element_id, OccupationFeature.category)
    ).all()
    education_labels = {
        row.category: row.category_description
        for row in session.scalars(
            select(EducationCategory).where(EducationCategory.snapshot_id == snapshot.id)
        ).all()
    }
    education: list[OccupationEducationItem] = []
    activities: list[OccupationActivityItem] = []
    interests: list[OccupationFeatureItem] = []
    for row in feature_rows:
        if row.domain == "education" and row.category:
            education.append(
                OccupationEducationItem(
                    category=row.category,
                    description=education_labels.get(row.category, row.element_name),
                    percent=float(row.raw_value),
                )
            )
        elif row.domain == "work_activities":
            importance = float(row.used_value) if row.used_value is not None else float(row.raw_value)
            activities.append(
                OccupationActivityItem(
                    element_id=row.element_id,
                    name=row.element_name,
                    importance=importance,
                )
            )
        elif row.domain == "riasec" and row.include_in_knn:
            value = float(row.used_value) if row.used_value is not None else float(row.raw_value)
            interests.append(
                OccupationFeatureItem(
                    element_id=row.element_id,
                    element_name=row.element_name,
                    value=value,
                )
            )
    education.sort(key=lambda item: -item.percent)
    activities.sort(key=lambda item: (-(item.importance or 0), item.element_id))
    activities = activities[:8]
    return OccupationDetail(
        onetsoc_code=occupation.onetsoc_code,
        title=occupation.title,
        description=occupation.description,
        job_zone=occupation.job_zone,
        knn_complete=occupation.knn_complete,
        recommendable=occupation.recommendable,
        has_education=occupation.has_education,
        has_work_context=occupation.has_work_context,
        feature_version=snapshot.feature_version,
        onet_release=snapshot.onet_release,
        job_zone_name=zone_name,
        job_zone_education=zone_education,
        job_zone_experience=zone_experience,
        feature_count=int(
            session.scalar(
                select(func.count())
                .select_from(OccupationFeature)
                .where(OccupationFeature.occupation_id == occupation.id)
            )
            or 0
        ),
        education=education,
        work_activities=activities,
        interests=interests,
    )
