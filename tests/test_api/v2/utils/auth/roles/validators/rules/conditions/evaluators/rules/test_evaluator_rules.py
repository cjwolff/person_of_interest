import pytest
from fastapi import HTTPException
from app.api.v2.utils.auth.roles.validators.rules.conditions.evaluators.rules.evaluator_rules import EvaluatorRules  # Changed from ............api
from app.core.utils.security.auth.jwt import generate_jwt  # Changed from ............core 