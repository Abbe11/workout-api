"""Seed the database with example data for every model.

Run with:  python -m server.seed   (or)   flask shell < ...

Creates Exercises, Workouts, and the WorkoutExercise links that join
them, demonstrating that a single exercise can be reused across many
workouts with different sets / reps / duration.
"""

from datetime import date, timedelta

from server.config import create_app, db
from server.models import Exercise, Workout, WorkoutExercise


def seed():
    app = create_app()
    with app.app_context():
        print("Clearing existing data...")
        WorkoutExercise.query.delete()
        Workout.query.delete()
        Exercise.query.delete()
        db.session.commit()

        print("Seeding exercises...")
        squat = Exercise(name="Back Squat", category="strength", equipment="Barbell")
        bench = Exercise(name="Bench Press", category="strength", equipment="Barbell")
        plank = Exercise(name="Plank", category="core", equipment="Bodyweight")
        run = Exercise(name="Treadmill Run", category="cardio", equipment="Treadmill")
        stretch = Exercise(
            name="Hamstring Stretch", category="mobility", equipment="Mat"
        )
        db.session.add_all([squat, bench, plank, run, stretch])
        db.session.commit()

        print("Seeding workouts...")
        leg_day = Workout(
            title="Leg Day",
            date=date.today(),
            duration_minutes=60,
            notes="Focus on depth and control.",
        )
        push_day = Workout(
            title="Push Day",
            date=date.today() - timedelta(days=2),
            duration_minutes=45,
            notes="Upper-body pressing.",
        )
        conditioning = Workout(
            title="Conditioning",
            date=date.today() - timedelta(days=4),
            duration_minutes=30,
        )
        db.session.add_all([leg_day, push_day, conditioning])
        db.session.commit()

        print("Linking exercises to workouts...")
        links = [
            # Leg Day
            WorkoutExercise(workout=leg_day, exercise=squat, sets=5, reps=5),
            WorkoutExercise(workout=leg_day, exercise=plank, duration_seconds=60),
            WorkoutExercise(workout=leg_day, exercise=stretch, duration_seconds=120),
            # Push Day (reuses bench + plank)
            WorkoutExercise(workout=push_day, exercise=bench, sets=4, reps=8),
            WorkoutExercise(workout=push_day, exercise=plank, duration_seconds=45),
            # Conditioning (reuses the treadmill run)
            WorkoutExercise(workout=conditioning, exercise=run, duration_seconds=1200),
        ]
        db.session.add_all(links)
        db.session.commit()

        print(
            f"Done. {Exercise.query.count()} exercises, "
            f"{Workout.query.count()} workouts, "
            f"{WorkoutExercise.query.count()} links."
        )


if __name__ == "__main__":
    seed()
