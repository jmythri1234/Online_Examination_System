🎓 ExamPro – Online Examination System

A web-based examination platform developed using Python and Flask to manage online exams, evaluate student performance, and provide examination analytics through an intuitive dashboard.

✨ Key Features

- 🔐 User Authentication – Separate login access for administrators and students.
- 📝 Exam Management – Create examinations and manage questions.
- 💻 Online Assessments – Allow students to attempt exams and submit answers.
- 📊 Performance Analytics – Visualize pass/fail statistics and exam-wise average scores.
- 🏆 Result Management – Display examination scores and results.
- 📚 Exam History – Track previous examination attempts.
- 📷 Camera Monitoring – Provide camera preview and record proctoring events.
- 🛡️ Admin Dashboard – Manage examinations, review performance, and view proctoring logs.

🛠️ Tech Stack

Technology| Purpose
Python| Core programming language
Flask| Web application framework
SQLite| Database
Flask-SQLAlchemy| Database integration
Flask-Login| User authentication
HTML & CSS| Web page structure and styling
JavaScript| Client-side functionality
Chart.js| Performance analytics and charts
OpenCV| Camera-related functionality

📂 Project Structure

ExamPro/
├── app.py
├── requirements.txt
├── .gitignore
├── static/
│   └── css/
│       ├── style.css
│       └── exam.js
├── templates/
│   ├── add_question.html
│   ├── admin_dashboard.html
│   ├── create_exam.html
│   ├── exam_history.html
│   ├── exam_result.html
│   ├── index.html
│   ├── login.html
│   ├── proctoring_logs.html
│   ├── register.html
│   ├── student_dashboard.html
│   └── take_exam.html
└── screenshots/

⚙️ Installation & Setup

1. Clone the repository

git clone https://github.com/jmythri1234/Online_Examination_System.git
cd Online_Examination_System

2. Create a virtual environment

python -m venv venv

3. Activate the environment

Windows:

.\venv\Scripts\Activate.ps1

4. Install dependencies

pip install -r requirements.txt

5. Start the application

python app.py

Open your browser and visit:

"http://127.0.0.1:5000"

📸 Screenshots

Home Page

Admin Dashboard & Analytics

Admin Dashboard (Screenshots)

Student Dashboard

Student Dashboard (Screenshots)

Online Examination

Exam Result

Exam History

🔒 Security & Privacy

- Uses password-hashing utilities for secure password storage.
- Restricts protected pages based on user authentication.
- Excludes local database files and sensitive environment files from version control.
- Camera monitoring should be used transparently and with appropriate user consent.

🚀 Future Enhancements

- Timed examinations and automatic submission.
- Enhanced proctoring capabilities.
- Downloadable performance reports.
- Additional question types and examination settings.
- Improved accessibility and responsive design.

🎯 Project Objective

ExamPro demonstrates the development of a complete online examination workflow, combining authentication, exam management, result tracking, database integration, and performance analytics in a single web application.

---

Developed with Python, Flask, and modern web technologies.

⭐ If you find this project useful, consider starring the repository!
