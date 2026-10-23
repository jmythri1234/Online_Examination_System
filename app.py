from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, jsonify
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import secrets

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", secrets.token_hex(32)
)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + (INSTANCE_DIR / "exam.db").as_posix()
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# ---------------- DATABASE MODELS ----------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="student", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, default="")
    duration = db.Column(db.Integer, nullable=False, default=30)
    created_at = db.Column(db.DateTime, default=datetime.now)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(
        db.Integer, db.ForeignKey("exam.id"), nullable=False
    )
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)


class ExamAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False
    )
    exam_id = db.Column(
        db.Integer, db.ForeignKey("exam.id"), nullable=False
    )
    score = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, default=datetime.now)
    submitted_at = db.Column(db.DateTime)


class ProctoringEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(
        db.Integer, db.ForeignKey("exam_attempt.id"), nullable=False
    )
    event_type = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.now)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Please fill in all required fields.", "error")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        existing_user = db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one_or_none()

        if existing_user:
            flash("An account with this email already exists.", "error")
            return render_template("register.html")

        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role="student"
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one_or_none()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "admin":
        return redirect(url_for("admin_dashboard"))

    exams = db.session.execute(
        db.select(Exam).order_by(Exam.id.desc())
    ).scalars().all()

    attempts = db.session.execute(
        db.select(ExamAttempt)
        .filter_by(student_id=current_user.id)
        .order_by(ExamAttempt.id.desc())
    ).scalars().all()

    return render_template(
        "student_dashboard.html",
        exams=exams,
        attempts=attempts
    )


# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():

    if current_user.role != "admin":
        flash("Access denied. Admin account required.", "error")
        return redirect(url_for("dashboard"))

    # Fetch users
    users = db.session.execute(
        db.select(User).order_by(User.id.desc())
    ).scalars().all()

    # Fetch examinations
    exams = db.session.execute(
        db.select(Exam).order_by(Exam.id.desc())
    ).scalars().all()

    # Fetch exam attempts
    attempts = db.session.execute(
        db.select(ExamAttempt).order_by(
            ExamAttempt.id.desc()
        )
    ).scalars().all()

    # Basic analytics
    total_students = sum(
        1 for user in users if user.role == "student"
    )

    total_exams = len(exams)

    total_attempts = len(attempts)

    # Proctoring events count
    total_proctoring_events = db.session.execute(
        db.select(db.func.count(ProctoringEvent.id))
    ).scalar_one()

    # Only submitted attempts with valid question totals
    submitted_attempts = [
        attempt for attempt in attempts
        if attempt.submitted_at is not None
        and attempt.total_questions > 0
    ]

    # Calculate percentages
    percentages = [
        (attempt.score / attempt.total_questions) * 100
        for attempt in submitted_attempts
    ]

    # Average percentage
    average_score = (
        round(sum(percentages) / len(percentages), 2)
        if percentages else 0
    )

    # Highest percentage
    highest_score = (
        round(max(percentages), 2)
        if percentages else 0
    )

    # Pass and fail counts
    pass_count = sum(
        1 for percentage in percentages
        if percentage >= 50
    )

    fail_count = sum(
        1 for percentage in percentages
        if percentage < 50
    )

    # Exam-wise performance analytics
    exam_performance = []

    for exam in exams:
        exam_attempts = [
            attempt for attempt in submitted_attempts
            if attempt.exam_id == exam.id
        ]

        exam_percentages = [
            (attempt.score / attempt.total_questions) * 100
            for attempt in exam_attempts
        ]

        exam_average = (
            round(sum(exam_percentages) / len(exam_percentages), 2)
            if exam_percentages else 0
        )

        exam_performance.append({
            "title": exam.title,
            "average": exam_average
        })
    return render_template(
        "admin_dashboard.html",
        users=users,
        exams=exams,
        attempts=attempts,
        total_students=total_students,
        total_exams=total_exams,
        total_attempts=total_attempts,
        total_proctoring_events=total_proctoring_events,
        average_score=average_score,
        highest_score=highest_score,
        pass_count=pass_count,
        fail_count=fail_count,
        
        exam_performance=exam_performance

    )


# ---------------- ADMIN PROCTORING LOGS ----------------

@app.route("/admin/proctoring-logs")
@login_required
def admin_proctoring_logs():
    if current_user.role != "admin":
        flash("Access denied. Admin account required.", "error")
        return redirect(url_for("dashboard"))

    events = db.session.execute(
        db.select(ProctoringEvent)
        .order_by(ProctoringEvent.created_at.desc())
    ).scalars().all()

    event_details = []

    for event in events:
        attempt = db.session.get(ExamAttempt, event.attempt_id)

        student = db.session.get(User, attempt.student_id) if attempt else None
        exam = db.session.get(Exam, attempt.exam_id) if attempt else None

        event_details.append({
            "id": event.id,
            "attempt_id": event.attempt_id,
            "student_name": student.name if student else "Unknown",
            "exam_name": exam.title if exam else "Unknown",
            "event_type": event.event_type,
            "details": event.details,
            "created_at": event.created_at
        })

    return render_template(
        "proctoring_logs.html",
        events=event_details
    )


# ---------------- CREATE EXAM ----------------

@app.route("/admin/create-exam", methods=["GET", "POST"])
@login_required
def create_exam():
    if current_user.role != "admin":
        flash("Access denied. Admins only.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        duration_text = request.form.get("duration", "").strip()

        if not title:
            flash("Please enter an exam title.", "error")
            return redirect(url_for("create_exam"))

        try:
            duration = int(duration_text)
        except (ValueError, TypeError):
            flash("Please enter a valid exam duration.", "error")
            return redirect(url_for("create_exam"))

        if duration < 1 or duration > 300:
            flash(
                "Duration must be between 1 and 300 minutes.",
                "error"
            )
            return redirect(url_for("create_exam"))

        exam = Exam(
            title=title,
            description=description,
            duration=duration
        )

        db.session.add(exam)
        db.session.commit()

        flash("Exam created successfully!", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("create_exam.html")


    # ---------------- ADD QUESTION ----------------

@app.route("/admin/exam/<int:exam_id>/add-question", methods=["GET", "POST"])
@login_required
def add_question(exam_id):
    if current_user.role != "admin":
        flash("Access denied. Admins only.", "error")
        return redirect(url_for("dashboard"))

    exam = db.session.get(Exam, exam_id)

    if exam is None:
        flash("Exam not found.", "error")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        question_text = request.form.get("question_text", "").strip()
        option_a = request.form.get("option_a", "").strip()
        option_b = request.form.get("option_b", "").strip()
        option_c = request.form.get("option_c", "").strip()
        option_d = request.form.get("option_d", "").strip()
        correct_answer = request.form.get("correct_answer", "").strip().upper()

        if not all([
            question_text,
            option_a,
            option_b,
            option_c,
            option_d
        ]):
            flash("Please fill in all question fields.", "error")
            return render_template("add_question.html", exam=exam)

        if correct_answer not in ["A", "B", "C", "D"]:
            flash("Please select a valid correct answer.", "error")
            return render_template("add_question.html", exam=exam)

        question = Question(
            exam_id=exam.id,
            question_text=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_answer=correct_answer
        )

        db.session.add(question)
        db.session.commit()

        flash("Question added successfully!", "success")
        return render_template("add_question.html", exam=exam)

    return render_template("add_question.html", exam=exam)


# ---------------- START EXAM ----------------

@app.route("/exam/<int:exam_id>/start")
@login_required
def start_exam(exam_id):
    if current_user.role != "student":
        flash("Only students can take examinations.", "error")
        return redirect(url_for("dashboard"))

    exam = db.session.get(Exam, exam_id)

    if exam is None:
        flash("Exam not found.", "error")
        return redirect(url_for("dashboard"))

    questions = db.session.execute(
        db.select(Question)
        .filter_by(exam_id=exam.id)
        .order_by(Question.id.asc())
    ).scalars().all()

    if not questions:
        flash("This exam has no questions yet.", "error")
        return redirect(url_for("dashboard"))

    # Find an existing unfinished attempt
    attempt = db.session.execute(
        db.select(ExamAttempt)
        .filter_by(
            student_id=current_user.id,
            exam_id=exam.id,
            submitted_at=None
        )
        .order_by(ExamAttempt.id.desc())
    ).scalars().first()

    # Create an attempt if one does not already exist
    if attempt is None:
        attempt = ExamAttempt(
            student_id=current_user.id,
            exam_id=exam.id,
            score=0,
            total_questions=len(questions),
            started_at=datetime.now()
        )
        db.session.add(attempt)
        db.session.commit()

    # Calculate remaining time using the original start time
    elapsed_seconds = (
        datetime.now() - attempt.started_at
    ).total_seconds()

    remaining_seconds = max(
        0,
        int(exam.duration * 60 - elapsed_seconds)
    )

    if remaining_seconds <= 0:
        attempt.submitted_at = datetime.now()
        db.session.commit()
        flash("The exam time has expired. Please check your exam history.", "error")
        return redirect(url_for("exam_history"))

    return render_template(
        "take_exam.html",
        exam=exam,
        questions=questions,
        attempt=attempt,
        remaining_seconds=remaining_seconds
    )


# ---------------- SUBMIT EXAM -----------------

@app.route("/exam/<int:exam_id>/submit", methods=["POST"])
@login_required
def submit_exam(exam_id):

    if current_user.role != "student":
        flash("Only students can submit examinations.", "error")
        return redirect(url_for("dashboard"))

    exam = db.session.get(Exam, exam_id)

    if exam is None:
        flash("Exam not found.", "error")
        return redirect(url_for("dashboard"))

    questions = db.session.execute(
        db.select(Question)
        .filter_by(exam_id=exam.id)
        .order_by(Question.id.asc())
    ).scalars().all()

    if not questions:
        flash("This exam has no questions.", "error")
        return redirect(url_for("dashboard"))

    # Validate attempt ID
    attempt_id = request.form.get("attempt_id", "").strip()

    if not attempt_id.isdigit():
        flash("Invalid exam attempt. Please start the exam again.", "error")
        return redirect(url_for("dashboard"))

    attempt = db.session.get(ExamAttempt, int(attempt_id))

    if (
        attempt is None
        or attempt.student_id != current_user.id
        or attempt.exam_id != exam.id
        or attempt.submitted_at is not None
        or attempt.started_at is None
    ):
        flash("Invalid or already submitted exam.", "error")
        return redirect(url_for("dashboard"))

    # Enforce the exam duration on the server
    elapsed_seconds = (
        datetime.now() - attempt.started_at
    ).total_seconds()

    allowed_seconds = exam.duration * 60

    if elapsed_seconds > allowed_seconds + 5:
        # Time expired: save the attempt as submitted
        attempt.score = 0
        attempt.total_questions = len(questions)
        attempt.submitted_at = datetime.now()

        db.session.commit()

        flash("Exam time expired. Your attempt has been recorded.", "error")
        return redirect(url_for("exam_history"))

    # Calculate score
    score = 0

    for question in questions:
        selected_answer = request.form.get(
            f"question_{question.id}", ""
        ).strip().upper()

        if selected_answer == question.correct_answer.upper():
            score += 1

    # Save result
    attempt.score = score
    attempt.total_questions = len(questions)
    attempt.submitted_at = datetime.now()

    db.session.commit()

    return render_template(
        "exam_result.html",
        exam=exam,
        attempt=attempt
    )
# ---------------- EXAM HISTORY ----------------

@app.route("/exam-history")
@login_required
def exam_history():
    attempts = db.session.execute(
        db.select(ExamAttempt)
        .filter_by(student_id=current_user.id)
        .order_by(ExamAttempt.id.desc())
    ).scalars().all()

    return render_template(
        "exam_history.html",
        attempts=attempts
    )


# ---------------- LOGOUT ----------------

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


# ---------------- DATABASE INITIALIZATION ----------------

with app.app_context():
    db.create_all()

@app.route("/proctoring/event", methods=["POST"])
@login_required
def save_proctoring_event():
    data = request.get_json(silent=True) or {}

    attempt_id = data.get("attempt_id")
    event_type = data.get("event_type")

    if not attempt_id or event_type != "tab_switch":
        return jsonify({"success": False}), 400

    attempt = db.session.get(ExamAttempt, attempt_id)

    if not attempt or attempt.student_id != current_user.id:
        return jsonify({"success": False}), 403

    if attempt.submitted_at is not None:
        return jsonify({"success": False}), 400

    event = ProctoringEvent(
        attempt_id=attempt.id,
        event_type="tab_switch",
        details="Student switched away from the exam tab."
    )

    db.session.add(event)
    db.session.commit()

    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)