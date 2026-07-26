# Workout Tracker API

A Flask + SQLAlchemy + Marshmallow backend for a workout tracking
application used by personal trainers. Trainers can create workouts,
maintain a library of reusable exercises, and attach exercises to
workouts with sets, reps, or duration recorded for each pairing.

## Description

The API tracks **workouts** and their associated **exercises**. Each
workout can include many exercises, and each exercise can be reused
across many workouts — a classic many-to-many relationship. Because
every pairing needs its own `sets` / `reps` / `duration`, the join is
modeled as an **association object** (`WorkoutExercise`) rather than a
plain association table.

Data integrity is enforced at three levels:

- **Table constraints** — `NOT NULL`, `UNIQUE`, and `CHECK` constraints
  in the database (e.g. positive workout duration, unique exercise
  names, an exercise can only appear once per workout).
- **Model validations** — Python `@validates` methods on the models
  (e.g. non-empty titles, category must be a known value, non-negative
  sets/reps).
- **Schema validations** — Marshmallow validation on incoming requests
  (`required`, `Length`, `Range`, `OneOf`, and a cross-field check that
  a logged exercise records at least one metric).

Per the spec, there are no update endpoints and no endpoint to remove an
exercise from a workout.

## Data Model

| Model            | Key fields                                           | Notes                                   |
| ---------------- | ---------------------------------------------------- | --------------------------------------- |
| `Workout`        | `title`, `date`, `duration_minutes`, `notes`         | A single training session               |
| `Exercise`       | `name` (unique), `category`, `equipment`             | A reusable movement                     |
| `WorkoutExercise`| `workout_id`, `exercise_id`, `sets`, `reps`, `duration_seconds` | Association object joining the two |

Relationships:

- `Workout` 1—∞ `WorkoutExercise` ∞—1 `Exercise` (many-to-many via the
  association object).
- Deleting a `Workout` or an `Exercise` cascades to its link rows only;
  it never deletes the other reusable side.

## Project Structure

```
workout-api/
├── Pipfile
├── README.md
├── GIT_WORKFLOW.md
├── .flaskenv
├── .gitignore
├── server/
│   ├── __init__.py
│   ├── app.py         # entry point (creates the app)
│   ├── config.py      # app factory + db/migrate instances
│   ├── models.py      # Workout, Exercise, WorkoutExercise
│   ├── schemas.py     # Marshmallow schemas + validations
│   ├── routes.py      # API blueprint (all endpoints)
│   └── seed.py        # example data for every model
└── tests/
    └── test_app.py    # pytest endpoint + validation tests
```

## Installation

```bash
# 1. Install dependencies into a virtual environment
pipenv install
pipenv shell

# 2. Initialize and migrate the database
flask db init        # only the first time, if migrations/ doesn't exist
flask db migrate -m "create workouts, exercises, workout_exercises"
flask db upgrade

# 3. Seed example data for all models
python -m server.seed
```

`FLASK_APP` is already set to `server/app.py` in `.flaskenv`, so the
`flask` commands above work without extra environment setup.

## Running

```bash
flask run
# API available at http://127.0.0.1:5555
```

Visit `http://127.0.0.1:5555/` for a JSON index of all endpoints.

## Running Tests

```bash
pipenv install --dev
pytest
```

## API Endpoints

| Method | Path                          | Description                                              |
| ------ | ----------------------------- | ------------------------------------------------------- |
| GET    | `/`                           | JSON index listing all endpoints                        |
| GET    | `/workouts`                   | List all workouts (with their exercises)                |
| GET    | `/workouts/<id>`              | Get a single workout and its exercises                  |
| POST   | `/workouts`                   | Create a workout                                        |
| DELETE | `/workouts/<id>`              | Delete a workout (and its link rows)                    |
| GET    | `/exercises`                  | List all exercises                                      |
| GET    | `/exercises/<id>`             | Get a single exercise                                   |
| POST   | `/exercises`                  | Create an exercise                                      |
| DELETE | `/exercises/<id>`             | Delete an exercise (and its link rows)                  |
| POST   | `/workouts/<id>/exercises`    | Add an exercise to a workout with sets/reps/duration    |

### Example requests

Create a workout:

```bash
curl -X POST http://127.0.0.1:5555/workouts \
  -H "Content-Type: application/json" \
  -d '{"title": "Leg Day", "duration_minutes": 60, "notes": "Squat focus"}'
```

Create an exercise:

```bash
curl -X POST http://127.0.0.1:5555/exercises \
  -H "Content-Type: application/json" \
  -d '{"name": "Back Squat", "category": "strength", "equipment": "Barbell"}'
```

Add an exercise to a workout:

```bash
curl -X POST http://127.0.0.1:5555/workouts/1/exercises \
  -H "Content-Type: application/json" \
  -d '{"exercise_id": 1, "sets": 5, "reps": 5}'
```

### Response codes

- `200` OK, `201` Created
- `400` Validation error (bad or missing fields)
- `404` Resource not found
- `409` Conflict (duplicate exercise name, or exercise already on the
  workout)

## Validation Summary

**Table constraints:** `NOT NULL` on required columns; `UNIQUE` on
`exercises.name`; `UNIQUE(workout_id, exercise_id)`; `CHECK` for
positive workout duration and non-negative sets/reps/duration.

**Model validations:** non-empty/valid-length titles and names;
positive `duration_minutes`; `category` restricted to a known set;
non-negative `sets`/`reps`/`duration_seconds`.

**Schema validations:** `required` fields; `Length` on strings; `Range`
on numeric fields; `OneOf` on `category`; a `@validates_schema` rule
requiring at least one of `sets`, `reps`, or `duration_seconds`.

## Tech Stack

Python 3.8+, Flask 2.2.2, Flask-Migrate 3.1.0, Flask-SQLAlchemy 3.0.3,
Marshmallow 3.20.1, SQLite.
