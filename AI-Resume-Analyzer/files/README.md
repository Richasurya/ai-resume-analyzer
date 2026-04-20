# 🤖 AI Resume Analyzer — CLI Tool

A beginner-friendly **command-line Python project** that reads a resume (PDF or TXT),
extracts key information using NLP, scores it out of 100, and gives actionable tips.

---

## 📁 Project Structure

```
resume_analyzer/
├── resume_analyzer.py   ← Main program (run this)
├── sample_resume.txt    ← Test resume to try right away
├── requirements.txt     ← Python dependencies
└── README.md            ← You are here
```

---

## ⚙️ Setup — Step by Step

### Step 1 — Make sure Python 3.10+ is installed
```bash
python --version
```

### Step 2 — (Optional but recommended) Create a virtual environment
```bash
python -m venv venv

# Activate it:
# macOS / Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

> NLTK data (punkt, stopwords) is downloaded automatically on first run.

---

## ▶️  How to Run

### Analyze the included sample resume (TXT)
```bash
python resume_analyzer.py sample_resume.txt
```

### Analyze your own PDF resume
```bash
python resume_analyzer.py /path/to/your_resume.pdf
```

### Analyze and save a JSON report
```bash
python resume_analyzer.py your_resume.pdf -o report.json
```

### Show help
```bash
python resume_analyzer.py --help
```

---

## 📊 What the Tool Does

| Feature | Details |
|---|---|
| **Text Extraction** | Reads PDF (via pdfminer) or plain TXT files |
| **Contact Info** | Extracts email, phone, LinkedIn, GitHub via Regex |
| **Skills** | Matches 80+ tech & 11 soft skills from a knowledge base |
| **Education** | Sentence-level NLP to find degree/university lines |
| **Experience** | Detects years of experience + date ranges |
| **Score (0–100)** | Weighted across 5 categories (see below) |
| **Suggestions** | Personalised tips based on what's missing |
| **JSON Export** | Full structured report saved with `-o` flag |

### Score Breakdown

| Category | Max Points | How it's calculated |
|---|---|---|
| Skills | 30 | 2 pts/tech skill (cap 20) + 2 pts/soft skill (cap 10) |
| Sections | 25 | % of 7 key sections present |
| Experience | 20 | years × 4 pts, capped at 20 |
| Action Verbs | 15 | 2 pts/verb, capped at 15 |
| Resume Length | 10 | Sweet spot: 300–800 words |

---

## 💡 Interview Talking Points

- **Why NLTK?** Lightweight, beginner-friendly, no model download needed
- **Why pdfminer over PyPDF2?** Better text extraction accuracy for complex layouts
- **Scoring system** — explain the weighted rubric and why each category matters
- **Extensibility** — swap keyword lists, add spaCy NER, or connect to a job description for gap analysis

---

## 🔧 Customisation Ideas (to impress interviewers)

1. **Add spaCy NER** to detect person names, org names automatically
2. **Job Description Match** — pass a JD file and show keyword overlap %
3. **ATS Simulation** — flag non-ATS-friendly formatting patterns
4. **Rich library** — replace plain print with coloured terminal output
5. **Export to PDF** — generate a nicely formatted PDF report

---

## 📦 Dependencies

```
nltk>=3.8.1          # NLP tokenisation & stopwords
pdfminer.six>=20221105  # PDF text extraction
```

Both are pure-Python, no C extensions or heavy models required.
