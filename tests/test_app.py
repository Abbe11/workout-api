"""End-to-end tests for the Workout API.

Run with:  pytest

Uses an in-memory SQLite database so tests never touch the real app.db.
"""

import pytest

from server.config import create_app, db
from server.models import Exercise, Workout


@pytest.fixture
def app():
    app = create_app("sqlite:///:memory:")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


# --- Workouts -------------------------------------------------------------- #
def test_create_and_get_workout(client):
    res = client.post("/workouts", json={"title": "Leg Day", "duration_minutes": 60})
    assert res.status_code == 201
    body = res.get_json()
    assert body["title"] == "Leg Day"

    res = client.get(f"/workouts/{body['id']}")
    assert res.status_code == 200
    assert res.get_json()["duration_minutes"] == 60


def test_list_workouts(client):
    client.post("/workouts", json={"title": "A Workout", "duration_minutes": 30})
    res = client.get("/workouts")
    assert res.status_code == 200
    assert len(res.get_json()) == 1


def test_delete_workout(client):
    res = client.post("/workouts", json={"title": "Temp", "duration_minutes": 20})
    wid = res.get_json()["id"]
    assert client.delete(f"/workouts/{wid}").status_code == 200
    assert client.get(f"/workouts/{wid}").status_code == 404


# --- Schema validation ----------------------------------------------------- #
def test_workout_requires_title(client):
    res = client.post("/workouts", json={"duration_minutes": 60})
    assert res.status_code == 400
    assert "title" in res.get_json()["errors"]


def test_workout_duration_must_be_positive(client):
    res = client.post("/workouts", json={"title": "Bad", "duration_minutes": 0})
    assert res.status_code == 400


# --- Exercises ------------------------------------------------------------- #
def test_create_exercise_and_category_validation(client):
    ok = client.post(
        "/exercises", json={"name": "Back Squat", "category": "strength"}
    )
    assert ok.status_code == 201

    bad = client.post(
        "/exercises", json={"name": "Mystery", "category": "not-a-category"}
    )
    assert bad.status_code == 400


def test_duplicate_exercise_name_conflicts(client):
    client.post("/exercises", json={"name": "Plank", "category": "core"})
    dup = client.post("/exercises", json={"name": "Plank", "category": "core"})
    assert dup.status_code == 409


# --- Adding an exercise to a workout --------------------------------------- #
def test_add_exercise_to_workout(client, app):
    w = client.post(
        "/workouts", json={"title": "Full Body", "duration_minutes": 45}
    ).get_json()
    e = client.post(
        "/exercises", json={"name": "Deadlift", "category": "strength"}
    ).get_json()

    res = client.post(
        f"/workouts/{w['id']}/exercises",
        json={"exercise_id": e["id"], "sets": 3, "reps": 5},
    )
    assert res.status_code == 201
    body = res.get_json()
    assert len(body["workout_exercises"]) == 1
    assert body["workout_exercises"][0]["exercise"]["name"] == "Deadlift"


def test_add_exercise_requires_a_metric(client):
    w = client.post(
        "/workouts", json={"title": "Metric Test", "duration_minutes": 45}
    ).get_json()
    e = client.post(
        "/exercises", json={"name": "Row", "category": "strength"}
    ).get_json()

    res = client.post(
        f"/workouts/{w['id']}/exercises", json={"exercise_id": e["id"]}
    )
    assert res.status_code == 400


def test_cannot_add_same_exercise_twice(client):
    w = client.post(
        "/workouts", json={"title": "Dup Link", "duration_minutes": 45}
    ).get_json()
    e = client.post(
        "/exercises", json={"name": "Pull Up", "category": "strength"}
    ).get_json()

    payload = {"exercise_id": e["id"], "reps": 10}
    assert client.post(f"/workouts/{w['id']}/exercises", json=payload).status_code == 201
    assert client.post(f"/workouts/{w['id']}/exercises", json=payload).status_code == 409
