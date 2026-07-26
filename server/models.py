"""SQLAlchemy models for the Workout API.

Entity design
-------------
* Workout            -- a single training session.
* Exercise           -- a reusable movement (e.g. "Back Squat").
* WorkoutExercise    -- association object linking a Workout to an
                        Exercise while carrying the sets / reps /
                        duration for that pairing.

Workout <-> Exercise is a many-to-many relationship implemented with an
association object so each pairing can store its own set/rep/duration
data. The same Exercise can therefore be reused across many Workouts.

Three layers of data integrity are applied here:
  1. Table constraints  -- enforced by the database (NOT NULL, UNIQUE,
                           CHECK).
  2. Model validations  -- enforced in Python via @validates before a
                           value is ever written.
"""

from datetime import date

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import validates

from server.config import db

VALID_CATEGORIES = {"strength", "cardio", "mobility", "balance", "core"}


class Workout(db.Model):
    __tablename__ = "workouts"

    # --- Table constraints -------------------------------------------------
    __table_args__ = (
        CheckConstraint("duration_minutes > 0", name="duration_positive"),
        CheckConstraint("length(title) >= 2", name="title_min_length"),
    )

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)          # NOT NULL constraint
    date = db.Column(db.Date, nullable=False, default=date.today)
    duration_minutes = db.Column(db.Integer, nullable=False)   # NOT NULL + CHECK
    notes = db.Column(db.String(500))

    # Association object relationship. Cascade means deleting a workout
    # also removes its link rows (but never the reusable Exercise rows).
    workout_exercises = db.relationship(
        "WorkoutExercise",
        back_populates="workout",
        cascade="all, delete-orphan",
    )
    # Convenience: read the linked Exercise objects directly.
    exercises = association_proxy("workout_exercises", "exercise")

    # --- Model validations -------------------------------------------------
    @validates("title")
    def validate_title(self, key, value):
        if value is None or not value.strip():
            raise ValueError("Workout title is required.")
        if len(value.strip()) < 2:
            raise ValueError("Workout title must be at least 2 characters.")
        return value.strip()

    @validates("duration_minutes")
    def validate_duration(self, key, value):
        if value is None:
            raise ValueError("duration_minutes is required.")
        if not isinstance(value, int) or value <= 0:
            raise ValueError("duration_minutes must be a positive integer.")
        return value

    def __repr__(self):
        return f"<Workout {self.id} {self.title!r}>"


class Exercise(db.Model):
    __tablename__ = "exercises"

    # --- Table constraints -------------------------------------------------
    __table_args__ = (
        UniqueConstraint("name", name="uq_exercise_name"),
        CheckConstraint("length(name) >= 2", name="name_min_length"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)  # NOT NULL + UNIQUE
    category = db.Column(db.String(50), nullable=False)
    equipment = db.Column(db.String(120))

    workout_exercises = db.relationship(
        "WorkoutExercise",
        back_populates="exercise",
        cascade="all, delete-orphan",
    )
    workouts = association_proxy("workout_exercises", "workout")

    # --- Model validations -------------------------------------------------
    @validates("name")
    def validate_name(self, key, value):
        if value is None or not value.strip():
            raise ValueError("Exercise name is required.")
        return value.strip()

    @validates("category")
    def validate_category(self, key, value):
        if value is None or value.strip().lower() not in VALID_CATEGORIES:
            allowed = ", ".join(sorted(VALID_CATEGORIES))
            raise ValueError(f"category must be one of: {allowed}.")
        return value.strip().lower()

    def __repr__(self):
        return f"<Exercise {self.id} {self.name!r}>"


class WorkoutExercise(db.Model):
    """Association object: one Exercise inside one Workout."""

    __tablename__ = "workout_exercises"

    # --- Table constraints -------------------------------------------------
    __table_args__ = (
        # An exercise can only appear once per workout.
        UniqueConstraint("workout_id", "exercise_id", name="uq_workout_exercise"),
        CheckConstraint("sets IS NULL OR sets >= 0", name="sets_non_negative"),
        CheckConstraint("reps IS NULL OR reps >= 0", name="reps_non_negative"),
        CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds >= 0",
            name="duration_seconds_non_negative",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(
        db.Integer, db.ForeignKey("workouts.id"), nullable=False
    )
    exercise_id = db.Column(
        db.Integer, db.ForeignKey("exercises.id"), nullable=False
    )
    sets = db.Column(db.Integer)
    reps = db.Column(db.Integer)
    duration_seconds = db.Column(db.Integer)

    workout = db.relationship("Workout", back_populates="workout_exercises")
    exercise = db.relationship("Exercise", back_populates="workout_exercises")

    # --- Model validations -------------------------------------------------
    @validates("sets", "reps", "duration_seconds")
    def validate_non_negative(self, key, value):
        if value is not None and (not isinstance(value, int) or value < 0):
            raise ValueError(f"{key} must be a non-negative integer.")
        return value

    def __repr__(self):
        return f"<WorkoutExercise w={self.workout_id} e={self.exercise_id}>"
