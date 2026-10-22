from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import Session, select

from app.database import SessionDep
from app.models import (
    Hero, HeroCreate, HeroPublic, HeroUpdate,
    Mission, MissionPublic, Team,
)

router = APIRouter(prefix="/heroes", tags=["heroes"])

NOT_FOUND = {404: {"description": "Hero not found"}}


def get_hero_or_404(session: Session, hero_id: int) -> Hero:
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero


def check_team_exists(session: Session, team_id: int | None) -> None:
    """An unknown team_id is a bad request (400), not a 500 from the foreign key."""
    if team_id is not None and not session.get(Team, team_id):
        raise HTTPException(status_code=400, detail=f"Team {team_id} does not exist")


@router.get("", response_model=list[HeroPublic], summary="List heroes")
def list_heroes(
    session: SessionDep,
    team_id: int | None = None,
    min_age: int | None = None,
    name: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
):
    """List heroes with optional filters: team, minimum age, and a case-insensitive part of the name."""
    query = select(Hero).order_by(Hero.id)
    if team_id is not None:
        query = query.where(Hero.team_id == team_id)
    if min_age is not None:
        query = query.where(Hero.age >= min_age)
    if name:
        query = query.where(Hero.name.ilike(f"%{name}%"))
    return session.exec(query.offset(offset).limit(limit)).all()


@router.get("/{hero_id}", response_model=HeroPublic,
            summary="Get one hero", responses=NOT_FOUND)
def read_hero(hero_id: int, session: SessionDep):
    """Return a single hero by its **id**."""
    return get_hero_or_404(session, hero_id)


@router.post("", response_model=HeroPublic, status_code=status.HTTP_201_CREATED,
             summary="Create a hero",
             responses={400: {"description": "Team does not exist"}})
def create_hero(hero_in: HeroCreate, session: SessionDep):
    """Create a hero. `team_id` is optional; if given, the team must exist."""
    check_team_exists(session, hero_in.team_id)
    hero = Hero.model_validate(hero_in)
    session.add(hero)
    session.commit()
    session.refresh(hero)
    return hero


@router.patch("/{hero_id}", response_model=HeroPublic,
              summary="Update a hero partially",
              responses={**NOT_FOUND, 400: {"description": "Team does not exist"}})
def update_hero(hero_id: int, hero_in: HeroUpdate, session: SessionDep):
    """Update only the fields that are sent in the body."""
    hero = get_hero_or_404(session, hero_id)
    changes = hero_in.model_dump(exclude_unset=True)  # only fields the client sent
    check_team_exists(session, changes.get("team_id"))
    hero.sqlmodel_update(changes)
    session.add(hero)
    session.commit()
    session.refresh(hero)
    return hero


@router.delete("/{hero_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a hero", responses=NOT_FOUND)
def delete_hero(hero_id: int, session: SessionDep):
    """Delete a hero by its **id**. Returns no content on success."""
    hero = get_hero_or_404(session, hero_id)
    session.delete(hero)
    session.commit()


@router.post("/{hero_id}/missions/{mission_id}", status_code=status.HTTP_204_NO_CONTENT,
             summary="Assign a mission to a hero",
             responses={404: {"description": "Hero or mission not found"}})
def assign_mission(hero_id: int, mission_id: int, session: SessionDep):
    """Link a mission to a hero. Assigning the same mission twice does nothing."""
    hero = session.get(Hero, hero_id)
    mission = session.get(Mission, mission_id)
    if not hero or not mission:
        raise HTTPException(status_code=404, detail="Hero or mission not found")
    if mission not in hero.missions:
        hero.missions.append(mission)      # SQLModel inserts the link row
        session.add(hero)
        session.commit()


@router.get("/{hero_id}/missions", response_model=list[MissionPublic],
            summary="List a hero's missions", responses=NOT_FOUND)
def list_hero_missions(hero_id: int, session: SessionDep):
    """Return every mission assigned to the hero."""
    return get_hero_or_404(session, hero_id).missions
