import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.v1.middleware.auth import AuthMiddleware 