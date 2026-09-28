"""Recommendation package: ingest, student features, rules, KNN, pipeline."""

from app.recommendation.ingest import run_ingest
from app.recommendation.pipeline import recommend
from app.recommendation.student_features import build_student_vector

__all__ = ["run_ingest", "build_student_vector", "recommend"]
