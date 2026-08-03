"""Unit tests for repositories."""
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.organization import Organization
from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository


def test_organization_repository_crud(db: Session):
    repo = OrganizationRepository(db)
    
    # Create
    org = Organization(name="Unique Org", slug="unique-org")
    created = repo.create(org)
    assert created.id is not None
    assert created.name == "Unique Org"

    # Read
    fetched = repo.get(created.id)
    assert fetched is not None
    assert fetched.slug == "unique-org"

    # Update
    fetched.name = "Updated Org Name"
    updated = repo.update(fetched)
    assert updated.name == "Updated Org Name"

    # Delete
    repo.delete(updated)
    assert repo.get(created.id) is None


def test_user_repository_crud(db: Session):
    repo = UserRepository(db)
    
    user = User(email="repouser@example.com", password_hash="pw", full_name="Repo User")
    created = repo.create(user)
    assert created.id is not None

    fetched = repo.get(created.id)
    assert fetched.email == "repouser@example.com"
