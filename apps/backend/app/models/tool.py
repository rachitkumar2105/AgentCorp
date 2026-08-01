"""
Tool database model.
"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_model import BaseModel


class Tool(Base, BaseModel):
    """
    Represents a reusable tool that agents can invoke.
    """

    __tablename__ = "tools"

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    agents = relationship(
        "AgentTool",
        back_populates="tool",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Tool(id={self.id}, name='{self.name}')>"
