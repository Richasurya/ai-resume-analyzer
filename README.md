# 🤖 ATS Resume Analyzer — CLI Tool

Match your resume against **any Job Description** and get an ATS score out of 100!

---

## How to Run

### Step 1 — Install dependency
```bash
pip install pdfminer.six
```

### Step 2 — Run with your resume
```bash
python ats_analyzer.py resume.pdf
```

### Step 3 — Paste the Job Description
```
📋  PASTE YOUR JOB DESCRIPTION BELOW
    (Press ENTER twice when done)

[paste JD here]

[press Enter twice]
```

### Step 4 — See your ATS Score!
```
ATS MATCH SCORE
[████████████████████░░░░] 74%
🟡  GOOD MATCH — 74/100
```

---

## Save Report as JSON
```bash
python ats_analyzer.py resume.pdf -o result.json
```

---

## Score Breakdown

| Category | Max Marks | Logic |
|---|---|---|
| Keyword Match | 50 | % of JD keywords found in resume |
| Tech Skills | 25 | % of JD tech skills in resume |
| Soft Skills | 10 | Soft skill overlap |
| Experience | 10 | Resume exp vs JD required exp |
| Education | 5 | Degree mentioned |
| **Total** | **100** | |

---

## Files
```
ats_analyzer/
├── ats_analyzer.py   ← Main program
├── sample_jd.txt     ← Sample Job Description to test
├── requirements.txt  ← Dependencies
└── README.md
```

