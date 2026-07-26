"""Marshmallow schemas for serialization and request validation.

These schemas do two jobs:
  * Serialize (dump) model instances into JSON, including nested
    relationships.
  * Validate (load) incoming request payloads before they reach the
    models, giving clean 400 responses instead of raw DB errors.

Multiple schema-level validations are present: required fields,
Length, Range, OneOf, and a cross-field @validates_schema check.
"""

from marshmallow import (
    Schema,
    ValidationError,
    fields,
    validate,
    validates_schema,
)

from server.models import VALID_CATEGORIES


# --------------------------------------------------------------------------- #
# Exercise
# --------------------------------------------------------------------------- #
class ExerciseSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=120),
    )
    category = fields.Str(
        required=True,
        validate=validate.OneOf(sorted(VALID_CATEGORIES)),
    )
    equipment = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=120),
    )


# --------------------------------------------------------------------------- #
# WorkoutExercise (association object)
# --------------------------------------------------------------------------- #
class WorkoutExerciseSchema(Schema):
    """Serializes a link row, flattening the exercise details in."""

    id = fields.Int(dump_only=True)
    exercise_id = fields.Int(required=True)
    sets = fields.Int(allow_none=True, validate=validate.Range(min=0))
    reps = fields.Int(allow_none=True, validate=validate.Range(min=0))
    duration_seconds = fields.Int(allow_none=True, validate=validate.Range(min=0))
    # Nested, read-only view of the linked exercise.
    exercise = fields.Nested(
        ExerciseSchema, dump_only=True, only=("id", "name", "category", "equipment")
    )

    @validates_schema
    def at_least_one_metric(self, data, **kwargs):
        """A logged exercise must record sets, reps, or duration."""
        if not any(
            data.get(field) is not None
            for field in ("sets", "reps", "duration_seconds")
        ):
            raise ValidationError(
                "Provide at least one of: sets, reps, or duration_seconds.",
                field_name="sets",
            )


# --------------------------------------------------------------------------- #
# Workout
# --------------------------------------------------------------------------- #
class WorkoutSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=120),
    )
    date = fields.Date(required=False)
    duration_minutes = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=1440),  # 1 min .. 24 hrs
    )
    notes = fields.Str(
        required=False, allow_none=True, validate=validate.Length(max=500)
    )
    # Read-only nested list of the exercises attached to this workout.
    workout_exercises = fields.Nested(
        WorkoutExerciseSchema, many=True, dump_only=True
    )


# Reusable schema instances.
exercise_schema = ExerciseSchema()
exercises_schema = ExerciseSchema(many=True)
workout_schema = WorkoutSchema()
workouts_schema = WorkoutSchema(many=True)
workout_exercise_schema = WorkoutExerciseSchema()
