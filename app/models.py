from datetime import datetime, timezone
from enum import Enum

from pydantic import field_validator
from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)  # timezone-aware


# ---------- Team ----------
class TeamBase(SQLModel):
    name: str = Field(index=True, unique=True, min_length=1, max_length=50,
                      schema_extra={"examples": ["Avengers"]})
    headquarters: str = Field(schema_extra={"examples": ["New York"]})


class Team(TeamBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    heroes: list["Hero"] = Relationship(back_populates="team")


class TeamCreate(TeamBase):
    pass


class TeamPublic(TeamBase):
    id: int


# ---------- Hero <-> Mission link (many-to-many) ----------
class HeroMissionLink(SQLModel, table=True):
    hero_id: int | None = Field(default=None, foreign_key="hero.id", primary_key=True)
    mission_id: int | None = Field(default=None, foreign_key="mission.id", primary_key=True)


# ---------- Hero ----------
class HeroStatus(str, Enum):
    active = "active"
    retired = "retired"


class HeroBase(SQLModel):
    name: str = Field(index=True, min_length=1, max_length=50,
                      schema_extra={"examples": ["Deadpond"]})
    age: int | None = Field(default=None, ge=0, le=1000,
                            schema_extra={"examples": [30]})
    power: str | None = None                 # Part 9: added with an Alembic migration
    status: HeroStatus = HeroStatus.active   # Part 10: added with an Alembic migration
    team_id: int | None = Field(default=None, foreign_key="team.id")


class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    secret_name: str
    created_at: datetime = Field(default_factory=utc_now,
                                 sa_type=DateTime(timezone=True))  # server sets it

    team: Team | None = Relationship(back_populates="heroes")
    missions: list["Mission"] = Relationship(back_populates="heroes",
                                             link_model=HeroMissionLink)


class HeroCreate(HeroBase):
    secret_name: str = Field(schema_extra={"examples": ["Dive Wilson"]})


class HeroPublic(HeroBase):
    id: int
    created_at: datetime


class HeroUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=50,
                             schema_extra={"examples": ["Deadpond"]})
    age: int | None = Field(default=None, ge=0, le=1000,
                            schema_extra={"examples": [31]})
    power: str | None = None
    status: HeroStatus | None = Field(default=None, schema_extra={"examples": ["retired"]})
    team_id: int | None = None               # null = remove the hero from its team
    secret_name: str | None = None

    @field_validator("name", "status", "secret_name")
    @classmethod
    def not_null(cls, value):
        # Only runs when the client sends the field: these columns are NOT NULL
        if value is None:
            raise ValueError("cannot be null")
        return value


# ---------- Mission ----------
class MissionBase(SQLModel):
    title: str


class Mission(MissionBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    heroes: list[Hero] = Relationship(back_populates="missions",
                                      link_model=HeroMissionLink)


class MissionCreate(MissionBase):
    pass


class MissionPublic(MissionBase):
    id: int
