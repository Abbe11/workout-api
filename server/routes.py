"""REST API endpoints for the Workout application.

Conventions
-----------
* Resources: /workouts, /exercises
* Nested action: POST /workouts/<id>/exercises adds an exercise to a
  workout (with sets / reps / duration).
* JSON in, JSON out. Validation errors return 400, missing resources
  return 404, and constraint conflicts return 409.

Per the spec there are intentionally no update (PUT/PATCH) endpoints and
no endpoint to remove an exercise from a workout.
"""

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from server.config import db
from server.models import Exercise, Workout, WorkoutExercise
from server.schemas import (
    exercise_schema,
    exercises_schema,
    workout_exercise_schema,
    workout_schema,
    workouts_schema,
)

api_bp = Blueprint("api", __name__)


# --------------------------------------------------------------------------- #
# Error handlers (registered on the blueprint)
# --------------------------------------------------------------------------- #
@api_bp.app_errorhandler(ValidationError)
def handle_marshmallow_error(err):
    return jsonify({"errors": err.messages}), 400


@api_bp.app_errorhandler(ValueError)
def handle_value_error(err):
    return jsonify({"error": str(err)}), 400


@api_bp.app_errorhandler(404)
def handle_not_found(err):
    return jsonify({"error": "Resource not found."}), 404


# --------------------------------------------------------------------------- #
# Index
# --------------------------------------------------------------------------- #
@api_bp.route("/")
def index():
    return jsonify(
        {
            "message": "Workout Tracker API",
            "endpoints": {
                "GET /workouts": "List all workouts",
                "GET /workouts/<id>": "Get a single workout",
                "POST /workouts": "Create a workout",
                "DELETE /workouts/<id>": "Delete a workout",
                "GET /exercises": "List all exercises",
                "GET /exercises/<id>": "Get a single exercise",
                "POST /exercises": "Create an exercise",
                "DELETE /exercises/<id>": "Delete an exercise",
                "POST /workouts/<id>/exercises": "Add an exercise to a workout",
            },
        }
    )


# --------------------------------------------------------------------------- #
# Workouts
# --------------------------------------------------------------------------- #
@api_bp.route("/workouts", methods=["GET"])
def list_workouts():
    workouts = Workout.query.order_by(Workout.date.desc()).all()
    return jsonify(workouts_schema.dump(workouts)), 200


@api_bp.route("/workouts/<int:workout_id>", methods=["GET"])
def get_workout(workout_id):
    workout = db.session.get(Workout, workout_id)
    if workout is None:
        return jsonify({"error": "Workout not found."}), 404
    return jsonify(workout_schema.dump(workout)), 200


@api_bp.route("/workouts", methods=["POST"])
def create_workout():
    payload = request.get_json() or {}
    data = workout_schema.load(payload)  # raises ValidationError -> 400

    workout = Workout(
        title=data["title"],
        duration_minutes=data["duration_minutes"],
        notes=data.get("notes"),
    )
    if data.get("date"):
        workout.date = data["date"]

    db.session.add(workout)
    db.session.commit()
    return jsonify(workout_schema.dump(workout)), 201


@api_bp.route("/workouts/<int:workout_id>", methods=["DELETE"])
def delete_workout(workout_id):
    workout = db.session.get(Workout, workout_id)
    if workout is None:
        return jsonify({"error": "Workout not found."}), 404

    db.session.delete(workout)
    db.session.commit()
    return jsonify({"message": f"Workout {workout_id} deleted."}), 200


# --------------------------------------------------------------------------- #
# Exercises
# --------------------------------------------------------------------------- #
@api_bp.route("/exercises", methods=["GET"])
def list_exercises():
    exercises = Exercise.query.order_by(Exercise.name).all()
    return jsonify(exercises_schema.dump(exercises)), 200


@api_bp.route("/exercises/<int:exercise_id>", methods=["GET"])
def get_exercise(exercise_id):
    exercise = db.session.get(Exercise, exercise_id)
    if exercise is None:
        return jsonify({"error": "Exercise not found."}), 404
    return jsonify(exercise_schema.dump(exercise)), 200


@api_bp.route("/exercises", methods=["POST"])
def create_exercise():
    payload = request.get_json() or {}
    data = exercise_schema.load(payload)

    exercise = Exercise(
        name=data["name"],
        category=data["category"],
        equipment=data.get("equipment"),
    )
    db.session.add(exercise)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "An exercise with that name already exists."}), 409

    return jsonify(exercise_schema.dump(exercise)), 201


@api_bp.route("/exercises/<int:exercise_id>", methods=["DELETE"])
def delete_exercise(exercise_id):
    exercise = db.session.get(Exercise, exercise_id)
    if exercise is None:
        return jsonify({"error": "Exercise not found."}), 404

    db.session.delete(exercise)
    db.session.commit()
    return jsonify({"message": f"Exercise {exercise_id} deleted."}), 200


# --------------------------------------------------------------------------- #
# Add an exercise to a workout
# --------------------------------------------------------------------------- #
@api_bp.route("/workouts/<int:workout_id>/exercises", methods=["POST"])
def add_exercise_to_workout(workout_id):
    workout = db.session.get(Workout, workout_id)
    if workout is None:
        return jsonify({"error": "Workout not found."}), 404

    payload = request.get_json() or {}
    data = workout_exercise_schema.load(payload)

    exercise = db.session.get(Exercise, data["exercise_id"])
    if exercise is None:
        return jsonify({"error": "Exercise not found."}), 404

    link = WorkoutExercise(
        workout_id=workout.id,
        exercise_id=exercise.id,
        sets=data.get("sets"),
        reps=data.get("reps"),
        duration_seconds=data.get("duration_seconds"),
    )
    db.session.add(link)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return (
            jsonify({"error": "That exercise is already on this workout."}),
            409,
        )

    return jsonify(workout_schema.dump(workout)), 201
