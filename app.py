from flask import Flask, request, jsonify, send_file
import fitz  # PyMuPDF
import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def screen_resume(resume_text, job_description):
    prompt = f"""
    You are a Senior Technical Recruiter with 20 years of experience.
    Your goal is to objectively evaluate a candidate based on a Job Description (JD).

    JOB DESCRIPTION:
    {job_description}

    CANDIDATE RESUME:
    {resume_text}

    TASK:
    Analyze the resume against the JD. Look for key skills, experience levels, and project relevance.
    Be strict but fair. "React" matches "React.js". "AWS" matches "Amazon Web Services".

    OUTPUT FORMAT:
    Provide the response in valid JSON format only. No extra text.
    {{
        "candidate_name": "extracted name",
        "match_score": 75,
        "key_strengths": ["strength 1", "strength 2", "strength 3"],
        "missing_critical_skills": ["skill 1", "skill 2"],
        "recommendation": "Interview",
        "reasoning": "A 2-sentence summary of why."
    }}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    return response.choices[0].message.content

@app.route("/")
def index():
    return send_file("resume.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        pdf_file = request.files.get("resume")
        job_description = request.form.get("job_description", "")

        if not pdf_file or not job_description:
            return jsonify({"error": "Resume aur JD dono zaroori hain!"}), 400

        resume_text = extract_text_from_pdf(pdf_file)
        result_string = screen_resume(resume_text, job_description)

        clean_json = result_string.replace("```json", "").replace("```", "").strip()
        result_data = json.loads(clean_json)

        return jsonify(result_data)

    except json.JSONDecodeError:
        return jsonify({"error": "AI response parse nahi hua. Dobara try karo."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
