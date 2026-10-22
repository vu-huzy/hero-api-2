from fastapi import APIRouter, status

from app.database import SessionDep
from app.models import Mission, MissionCreate, MissionPublic

router = APIRouter(prefix="/missions", tags=["missions"])


@router.post("", response_model=MissionPublic, status_code=status.HTTP_201_CREATED,
             summary="Create a mission")
def create_mission(mission_in: MissionCreate, session: SessionDep):
    """Create a mission that heroes can be assigned to."""
    mission = Mission.model_validate(mission_in)
    session.add(mission)
    session.commit()
    session.refresh(mission)
    return mission
