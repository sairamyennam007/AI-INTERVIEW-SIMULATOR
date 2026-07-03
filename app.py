from flask import Flask, render_template, request
from google import genai
from config import GEMINI_API_KEY
import PyPDF2
import sqlite3
import os
import re

app = Flask(__name__)

client = genai.Client(api_key=GEMINI_API_KEY)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

question_bank = {
    "Python": [
        "What is a list in Python?",
        "What is the difference between list and tuple?"
    ],
    "Java": [
        "What is OOP?",
        "What is inheritance?"
    ],
    "SQL": [
        "What is a primary key?",
        "What is a JOIN?"
    ],
    "HTML": [
        "What is a div tag?",
        "What is the difference between HTML and CSS?"
    ],
    "CSS": [
        "What is flexbox?",
        "What is the box model?"
    ]
}

interview_questions = []


def extract_text_from_pdf(path):
    text = ""

    with open(path, "rb") as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text

    return text


def get_skills(text):
    skills = []

    for skill in question_bank:
        if skill.lower() in text.lower():
            skills.append(skill)

    return skills


def save_result(score, total, percentage):
    connection = sqlite3.connect("interview.db")
    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO results(score, total, percentage) VALUES (?, ?, ?)",
        (score, total, percentage)
    )

    connection.commit()
    connection.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["GET", "POST"])
def upload():
    global interview_questions

    if request.method == "POST":
        resume = request.files["resume"]

        if resume.filename == "":
            return "Please select a file."

        file_path = os.path.join(UPLOAD_DIR, resume.filename)
        resume.save(file_path)

        resume_text = extract_text_from_pdf(file_path)
        skills = get_skills(resume_text)

        interview_questions = []

        for skill in skills:
            interview_questions.extend(question_bank[skill])

        if not interview_questions:
            interview_questions = [
                "Tell me about yourself.",
                "Why should we hire you?",
                "What are your strengths?"
            ]

        return render_template(
            "questions.html",
            questions=interview_questions
        )

    return render_template("upload.html")


@app.route("/result", methods=["POST"])
def result():
    total_score = 0
    feedback = []

    for index, question in enumerate(interview_questions):
        answer = request.form.get(
            f"answer{index + 1}",
            ""
        ).strip()

        if not answer:
            feedback.append(
                f"""
Question {index + 1}: {question}

Score: 0/10
Feedback: No answer provided.
Correct Answer: Please attempt this question.
"""
            )
            continue

        prompt = f"""
You are an expert technical interviewer.

Question:
{question}

Candidate Answer:
{answer}

Evaluate the answer.

Return ONLY in this format:

Score: X/10
Feedback: short explanation
Correct Answer: short ideal answer
"""

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            result_text = response.text

        except Exception as error:
            result_text = f"""
Question {index + 1}: {question}

Score: 0/10
Feedback: Gemini Error - {str(error)}
"""

        match = re.search(r"Score:\s*(\d+)", result_text)
        score = int(match.group(1)) if match else 0

        total_score += score
        feedback.append(result_text)

    total_marks = len(interview_questions) * 10
    percentage = round((total_score / total_marks) * 100, 2) if total_marks else 0

    save_result(total_score, total_marks, percentage)

    return render_template(
        "result.html",
        score=total_score,
        total=total_marks,
        percentage=percentage,
        feedback=feedback
    )


if __name__ == "__main__":
    app.run(debug=True)