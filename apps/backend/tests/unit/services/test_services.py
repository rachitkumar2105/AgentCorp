"""Unit tests for core services."""
import pytest
from sqlalchemy.orm import Session

from app.services.user_service import UserService
from app.services.organization_service import OrganizationService
from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository
from app.models.user import User
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate


def test_organization_service_logic(db: Session):
    repo = OrganizationRepository(db)
    svc = OrganizationService(repo)
    
    # Create Org
    org_in = OrganizationCreate(name="Service Org", slug="service-org", description="test description")
    org = svc.create(org_in)
    assert org.id is not None
    assert org.name == "Service Org"


def test_user_service_logic(db: Session):
    repo = UserRepository(db)
    svc = UserService(repo)
    
    # Create User
    user_obj = User(email="serviceuser@example.com", password_hash="securepassword", full_name="Service User")
    user = svc.create_user(user_obj)
    assert user.id is not None
    assert user.email == "serviceuser@example.com"
