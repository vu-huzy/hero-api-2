import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import Hero, Mission, Team


def make_team(session: Session) -> Team:
    team = Team(name="Avengers", headquarters="New York")
    session.add(team)
    session.commit()
    session.refresh(team)
    return team


def test_list_heroes(session: Session, client: TestClient):
    session.add(Hero(name="Tony", secret_name="Iron Man", age=45))
    session.commit()
    r = client.get("/api/v1/heroes")
    assert r.status_code == 200
    assert [h["name"] for h in r.json()] == ["Tony"]


def test_list_heroes_limit_over_100(client: TestClient):
    assert client.get("/api/v1/heroes?limit=101").status_code == 422


def test_read_hero(session: Session, client: TestClient):
    hero = Hero(name="Tony", secret_name="Iron Man")
    session.add(hero)
    session.commit()
    r = client.get(f"/api/v1/heroes/{hero.id}")
    assert r.status_code == 200
    assert r.json()["name"] == "Tony"


def test_read_hero_not_found(client: TestClient):
    r = client.get("/api/v1/heroes/999")
    assert r.status_code == 404
    assert r.json() == {"detail": "Hero not found"}


def test_create_hero(client: TestClient):
    r = client.post("/api/v1/heroes",
                    json={"name": "Deadpond", "secret_name": "Dive Wilson"})
    assert r.status_code == 201
    assert r.json()["name"] == "Deadpond"
    assert r.json()["status"] == "active"      # Enum -> value
    assert "secret_name" not in r.json()       # hidden by response_model


def test_create_hero_unknown_team(client: TestClient):
    r = client.post("/api/v1/heroes",
                    json={"name": "A", "secret_name": "a", "team_id": 999})
    assert r.status_code == 400


@pytest.mark.parametrize("payload", [
    {},                                                          # missing fields
    {"name": "X"},                                               # missing secret_name
    {"name": "X", "secret_name": "y", "age": "old"},             # wrong type
    {"name": "X", "secret_name": "y", "age": -5},                # ge=0
    {"name": "X", "secret_name": "y", "status": "dead"},         # not an enum value
])
def test_create_hero_invalid(client: TestClient, payload):
    assert client.post("/api/v1/heroes", json=payload).status_code == 422


def test_update_hero_partial(session: Session, client: TestClient):
    hero = Hero(name="Tony", secret_name="Iron Man", age=45)
    session.add(hero)
    session.commit()
    r = client.patch(f"/api/v1/heroes/{hero.id}", json={"status": "retired"})
    assert r.status_code == 200
    assert r.json()["age"] == 45
    assert r.json()["status"] == "retired"


def test_update_hero_not_found(client: TestClient):
    assert client.patch("/api/v1/heroes/999", json={"age": 1}).status_code == 404


def test_update_hero_unknown_team(session: Session, client: TestClient):
    hero = Hero(name="Tony", secret_name="Iron Man")
    session.add(hero)
    session.commit()
    r = client.patch(f"/api/v1/heroes/{hero.id}", json={"team_id": 999})
    assert r.status_code == 400


def test_update_hero_null_name(session: Session, client: TestClient):
    hero = Hero(name="Tony", secret_name="Iron Man")
    session.add(hero)
    session.commit()
    r = client.patch(f"/api/v1/heroes/{hero.id}", json={"name": None})
    assert r.status_code == 422


def test_delete_hero(session: Session, client: TestClient):
    hero = Hero(name="Tony", secret_name="Iron Man")
    session.add(hero)
    session.commit()
    assert client.delete(f"/api/v1/heroes/{hero.id}").status_code == 204
    assert client.get(f"/api/v1/heroes/{hero.id}").status_code == 404


def test_delete_hero_not_found(client: TestClient):
    assert client.delete("/api/v1/heroes/999").status_code == 404


def test_list_heroes_filter_by_team(session: Session, client: TestClient):
    team = make_team(session)
    session.add(Hero(name="Tony", secret_name="Iron Man", team_id=team.id))
    session.add(Hero(name="Peter", secret_name="Spider-Man"))
    session.commit()
    r = client.get(f"/api/v1/heroes?team_id={team.id}")
    assert [h["name"] for h in r.json()] == ["Tony"]


def test_create_mission(client: TestClient):
    r = client.post("/api/v1/missions", json={"title": "Battle of Sokovia"})
    assert r.status_code == 201
    assert r.json()["title"] == "Battle of Sokovia"


def test_assign_mission(session: Session, client: TestClient):
    hero = Hero(name="Tony", secret_name="Iron Man")
    mission = Mission(title="Battle of Sokovia")
    session.add_all([hero, mission])
    session.commit()
    r = client.post(f"/api/v1/heroes/{hero.id}/missions/{mission.id}")
    assert r.status_code == 204
    r = client.get(f"/api/v1/heroes/{hero.id}/missions")
    assert r.status_code == 200
    assert [m["title"] for m in r.json()] == ["Battle of Sokovia"]


def test_assign_mission_not_found(client: TestClient):
    assert client.post("/api/v1/heroes/999/missions/999").status_code == 404


def test_list_hero_missions_not_found(client: TestClient):
    assert client.get("/api/v1/heroes/999/missions").status_code == 404
