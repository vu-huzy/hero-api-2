from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import Hero, Team


def test_create_team(client: TestClient):
    r = client.post("/api/v1/teams", json={"name": "X-Men", "headquarters": "Westchester"})
    assert r.status_code == 201
    assert r.json()["name"] == "X-Men"


def test_create_team_duplicate(client: TestClient):
    body = {"name": "Avengers", "headquarters": "New York"}
    assert client.post("/api/v1/teams", json=body).status_code == 201
    assert client.post("/api/v1/teams", json=body).status_code == 409


def test_create_team_invalid(client: TestClient):
    r = client.post("/api/v1/teams", json={"name": "", "headquarters": "New York"})
    assert r.status_code == 422


def test_list_teams(session: Session, client: TestClient):
    session.add(Team(name="Avengers", headquarters="New York"))
    session.commit()
    r = client.get("/api/v1/teams")
    assert r.status_code == 200
    assert [t["name"] for t in r.json()] == ["Avengers"]


def test_list_team_heroes(session: Session, client: TestClient):
    team = Team(name="Avengers", headquarters="New York")
    session.add(team)
    session.commit()
    session.add(Hero(name="Tony", secret_name="Iron Man", team_id=team.id))
    session.commit()
    r = client.get(f"/api/v1/teams/{team.id}/heroes")
    assert r.status_code == 200
    assert [h["name"] for h in r.json()] == ["Tony"]


def test_list_team_heroes_not_found(client: TestClient):
    r = client.get("/api/v1/teams/999/heroes")
    assert r.status_code == 404
    assert r.json() == {"detail": "Team not found"}
