"""
Declarative Base compartida por todos los modelos ORM.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Clase base declarativa de SQLAlchemy 2.x."""
