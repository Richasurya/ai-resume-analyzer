"""
╔══════════════════════════════════════════════╗
║        AI RESUME ANALYZER - CLI TOOL        ║
║     Built with Python + NLP (Beginner)      ║
╚══════════════════════════════════════════════╝

Author  : You
Purpose : Analyze a resume PDF/TXT file and give
          a score, extracted info, and tips.
"""

import os
import re
import sys
import json
import argparse
from datetime import datetime

# ── Third-party imports ──────────────────────────────────────────────────────
try:
    from pdfminer.high_level import extract_text as pdf_extract
except ImportError:
    pdf_extract = None  # will warn user if they try a PDF

# ── Built-in NLP helpers (no NLTK data files required) ───────────────────────
# We use regex-based tokenisation so the tool works out of the box without
# downloading punkt / stopwords data — making it truly beginner-friendly.

# Common English stopwords (subset — enough for our keyword matching)
_STOPWORDS = {
    "a","an","the","and","or","but","in","on","at","to","for","of","with",
    "by","from","up","about","into","through","during","is","are","was",
    "were","be","been","being","have","has","had","do","does","did","will",
    "would","could","should","may","might","shall","can","need","dare",
    "ought","used","i","me","my","we","our","you","your","he","she","it",
    "its","they","them","their","what","which","who","this","that","these",
    "those","not","no","nor","so","yet","both","either","each","few","more",
    "most","other","some","such","than","too","very","just","also","as",
    "if","then","because","while","although","though","since","unless",
    "until","when","where","how","all","any","there","here",
}

def sent_tokenize(text: str) -> list[str]:
    """
    Simple regex sentence splitter — splits on '.', '!', '?' followed
    by whitespace or end-of-string.  Good enough for resume text.
    """
    # Split on sentence-ending punctuation
    raw = re.split(r"(?<=[.!?])\s+", text.strip())
    # Also split on newlines that look like section breaks
    sentences = []
    for chunk in raw:
        for line in chunk.split("\n"):
            line = line.strip()
            if line:
                sentences.append(line)
    return sentences

def word_tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokeniser."""
    return re.findall(r"\b[a-zA-Z]+\b", text)

def stopwords_set() -> set:
    return _STOPWORDS

# ─────────────────────────────────────────────────────────────────────────────
#  KNOWLEDGE BASE  –  edit these lists to customise the analyser
# ─────────────────────────────────────────────────────────────────────────────

TECH_SKILLS = [
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go",
    "rust", "swift", "kotlin", "php", "scala", "r", "matlab",
    # Web
    "html", "css", "react", "angular", "vue", "node.js", "nodejs", "django",
    "flask", "fastapi", "spring", "express", "next.js", "graphql", "rest api",
    # Data / ML
    "machine learning", "deep learning", "nlp", "computer vision", "tensorflow",
    "pytorch", "keras", "scikit-learn", "pandas", "numpy", "matplotlib",
    "seaborn", "tableau", "power bi", "data analysis", "data science",
    # Cloud / DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "jenkins",
    "terraform", "ansible", "linux", "bash", "git", "github", "gitlab",
    # Databases
    "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
    "firebase", "oracle", "sqlite",
    # Misc
    "agile", "scrum", "jira", "figma", "photoshop",
]

SOFT_SKILLS = [
    "communication", "leadership", "teamwork", "problem solving",
    "critical thinking", "time management", "adaptability", "creativity",
    "collaboration", "attention to detail", "project management",
]

# Education keywords to detect degree lines
EDUCATION_KEYWORDS = [
    "bachelor", "master", "phd", "b.sc", "m.sc", "b.tech", "m.tech",
    "b.e", "m.e", "mba", "b.com", "b.a", "m.a", "doctorate",
    "diploma", "associate", "degree", "university", "college", "institute",
    "school of", "academy",
]

# Experience section indicators
EXPERIENCE_KEYWORDS = [
    "experience", "work history", "employment", "professional background",
    "career history", "internship", "intern", "job", "position", "role",
    "worked at", "worked for",
]

# Strong action verbs boost the score
ACTION_VERBS = [
    "achieved", "built", "created", "designed", "developed", "engineered",
    "implemented", "improved", "increased", "launched", "led", "managed",
    "optimised", "optimized", "reduced", "spearheaded", "streamlined",
    "trained", "transformed",
]

# Important sections every good resume should have
IMPORTANT_SECTIONS = {
    "summary":    ["summary", "objective", "profile", "about me", "overview"],
    "skills":     ["skills", "technical skills", "core competencies", "expertise"],
    "education":  EDUCATION_KEYWORDS,
    "experience": EXPERIENCE_KEYWORDS,
    "projects":   ["projects", "personal projects", "academic projects", "portfolio"],
    "contact":    ["email", "phone", "linkedin", "github", "contact"],
    "certifications": ["certification", "certificate", "certified", "credential"],
}


# ─────────────────────────────────────────────────────────────────────────────
#  TEXT EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

def extract_text_from_pdf(path: str) -> str:
    """Use pdfminer to pull raw text from a PDF file."""
    if pdf_extract is None:
        print("❌  pdfminer.six is not installed.  Run: pip install pdfminer.six")
        sys.exit(1)
    try:
        text = pdf_extract(path)
        if not text or not text.strip():
            print("⚠️   The PDF appears to be image-only (scanned). "
                  "OCR support is not included; try a text-based PDF.")
            sys.exit(1)
        return text
    except Exception as exc:
        print(f"❌  Could not read PDF: {exc}")
        sys.exit(1)


def extract_text_from_txt(path: str) -> str:
    """Read a plain-text or .doc (text-only) file."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except Exception as exc:
        print(f"❌  Could not read file: {exc}")
        sys.exit(1)


def load_resume(path: str) -> str:
    """Dispatch to the right extractor based on file extension."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(path)
    elif ext in (".txt", ".text", ".doc"):
        return extract_text_from_txt(path)
    else:
        print(f"❌  Unsupported file type '{ext}'. Use .pdf or .txt")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
#  NLP HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Lowercase and strip extra whitespace."""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> list[str]:
    """Word-tokenise, remove stopwords and punctuation."""
    stop_words = stopwords_set()
    tokens = word_tokenize(text)
    return [t for t in tokens if t.isalpha() and t not in stop_words]


# ─────────────────────────────────────────────────────────────────────────────
#  ANALYSIS FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def extract_email(text: str) -> str | None:
    """Regex to grab the first email address found."""
    match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    """Regex for common phone formats."""
    match = re.search(
        r"(\+?\d[\d\s\-().]{7,}\d)", text
    )
    return match.group(0).strip() if match else None


def extract_linkedin(text: str) -> str | None:
    match = re.search(r"linkedin\.com/in/[\w\-]+", text, re.IGNORECASE)
    return match.group(0) if match else None


def extract_github(text: str) -> str | None:
    match = re.search(r"github\.com/[\w\-]+", text, re.IGNORECASE)
    return match.group(0) if match else None


def extract_skills(text_lower: str) -> dict:
    """
    Match tech and soft skills by scanning the cleaned resume text.
    Returns separate lists for tech and soft skills found.
    """
    found_tech  = [s for s in TECH_SKILLS  if s in text_lower]
    found_soft  = [s for s in SOFT_SKILLS  if s in text_lower]
    found_verbs = [v for v in ACTION_VERBS if v in text_lower]
    return {
        "tech":   sorted(set(found_tech)),
        "soft":   sorted(set(found_soft)),
        "action_verbs": sorted(set(found_verbs)),
    }


def extract_education(text: str) -> list[str]:
    """
    Return sentences that likely describe education.
    Strategy: sentence-tokenise → keep sentences containing edu keywords.
    """
    sentences = sent_tokenize(text)
    edu_lines = []
    for sent in sentences:
        sent_lower = sent.lower()
        if any(kw in sent_lower for kw in EDUCATION_KEYWORDS):
            # Keep only reasonable-length lines (skip headers / noise)
            cleaned = " ".join(sent.split())
            if 10 < len(cleaned) < 300:
                edu_lines.append(cleaned)
    return edu_lines[:5]  # return top 5 matches


def extract_experience(text: str) -> dict:
    """
    Estimate years of experience and find company/role mentions.
    Uses regex to find patterns like '3 years' or '2019 – 2022'.
    """
    years_mentioned = []

    # Pattern: "X years of experience" or "X+ years"
    year_patterns = re.findall(
        r"(\d+\.?\d*)\s*\+?\s*years?", text, re.IGNORECASE
    )
    years_mentioned = [float(y) for y in year_patterns]

    # Date ranges like 2019-2022 or Jan 2020 – Mar 2023
    date_ranges = re.findall(
        r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)?\.?\s*\d{4})"
        r"\s*[-–—to]+\s*"
        r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)?\.?\s*(?:\d{4}|present|current))",
        text, re.IGNORECASE,
    )

    # Estimate total years from date ranges
    calculated_years = 0.0
    for start_str, end_str in date_ranges:
        s_year = re.search(r"\d{4}", start_str)
        e_year = re.search(r"\d{4}", end_str)
        if s_year:
            s = int(s_year.group())
            e = int(e_year.group()) if e_year else datetime.now().year
            calculated_years += max(0, e - s)

    best_years = max(years_mentioned + [calculated_years], default=0)

    return {
        "estimated_years": round(best_years, 1),
        "date_ranges_found": len(date_ranges),
        "raw_year_mentions": years_mentioned,
    }


def detect_sections(text_lower: str) -> dict:
    """
    Check which important resume sections are present.
    Returns a dict: section_name → True/False
    """
    found = {}
    for section, keywords in IMPORTANT_SECTIONS.items():
        found[section] = any(kw in text_lower for kw in keywords)
    return found


# ─────────────────────────────────────────────────────────────────────────────
#  SCORING ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def calculate_score(skills: dict, sections: dict, experience: dict,
                    text_lower: str) -> dict:
    """
    Compute a score out of 100 across five weighted categories.

    Category            Max pts   Logic
    ──────────────────────────────────────────────────────────────
    Skills              30        tech(20) + soft(10)
    Sections present    25        ~3.5 pts per section (7 sections)
    Experience          20        years × 4, capped at 20
    Action verbs        15        2 pts each, capped at 15
    Resume length       10        word count sweet spot 300–800
    ──────────────────────────────────────────────────────────────
    """
    breakdown = {}

    # 1. Skills (30 pts)
    tech_pts = min(len(skills["tech"]) * 2,  20)   # 2 pts/skill, cap 20
    soft_pts = min(len(skills["soft"]) * 2,  10)   # 2 pts/skill, cap 10
    breakdown["skills"] = tech_pts + soft_pts

    # 2. Sections (25 pts)
    present = sum(1 for v in sections.values() if v)
    breakdown["sections"] = round(present / len(sections) * 25)

    # 3. Experience (20 pts)
    exp_pts = min(experience["estimated_years"] * 4, 20)
    breakdown["experience"] = round(exp_pts)

    # 4. Action verbs (15 pts)
    breakdown["action_verbs"] = min(len(skills["action_verbs"]) * 2, 15)

    # 5. Resume length (10 pts)
    word_count = len(text_lower.split())
    if 300 <= word_count <= 800:
        breakdown["length"] = 10
    elif 200 <= word_count < 300 or 800 < word_count <= 1200:
        breakdown["length"] = 7
    else:
        breakdown["length"] = 3

    total = sum(breakdown.values())
    return {"total": min(total, 100), "breakdown": breakdown}


# ─────────────────────────────────────────────────────────────────────────────
#  SUGGESTIONS ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def generate_suggestions(skills: dict, sections: dict, score: dict,
                          experience: dict) -> list[str]:
    """Return a prioritised list of actionable improvement tips."""
    tips = []

    # Missing sections
    missing = [s for s, present in sections.items() if not present]
    if missing:
        tips.append(
            f"📌  Add missing section(s): {', '.join(missing).title()}. "
            "Recruiters expect these."
        )

    # Too few tech skills
    if len(skills["tech"]) < 5:
        tips.append(
            f"🛠️   Only {len(skills['tech'])} tech skill(s) detected. "
            "List at least 8–12 relevant tools/technologies."
        )

    # No soft skills
    if not skills["soft"]:
        tips.append(
            "🤝  No soft skills found. Add 3–5 (e.g., leadership, "
            "communication, teamwork)."
        )

    # Weak action verbs
    if len(skills["action_verbs"]) < 4:
        tips.append(
            "💬  Use more strong action verbs (achieved, built, led, reduced…) "
            "in your bullet points."
        )

    # Experience
    if experience["estimated_years"] == 0 and experience["date_ranges_found"] == 0:
        tips.append(
            "📅  No work dates or experience years detected. "
            "Add date ranges (e.g., 'Jan 2021 – Dec 2023') to each role."
        )

    # Score-based generic advice
    total = score["total"]
    if total < 40:
        tips.append(
            "⚠️   Overall score is low. Focus on adding more keywords, "
            "quantified achievements, and a clear structure."
        )
    elif total < 60:
        tips.append(
            "📈  Good start! Quantify your achievements "
            "(e.g., 'Increased performance by 30%') to stand out."
        )
    elif total < 80:
        tips.append(
            "✅  Solid resume. Consider adding a GitHub or portfolio link "
            "and tailoring skills to the job description."
        )
    else:
        tips.append(
            "🌟  Great resume! Keep it updated and tailor it for each role."
        )

    return tips


# ─────────────────────────────────────────────────────────────────────────────
#  DISPLAY HELPERS
# ─────────────────────────────────────────────────────────────────────────────

WIDTH = 60  # terminal width for formatting

def divider(char="─"):
    print(char * WIDTH)

def header(title: str):
    print()
    divider("═")
    print(f"  {title}")
    divider("═")

def section_title(title: str):
    print()
    print(f"  ▶  {title}")
    divider()

def score_bar(score: int) -> str:
    """ASCII progress bar for the score."""
    filled = int(score / 100 * 40)
    bar    = "█" * filled + "░" * (40 - filled)
    return f"[{bar}] {score}/100"

def grade(score: int) -> str:
    if score >= 85: return "A  ★★★★★  Excellent"
    if score >= 70: return "B  ★★★★☆  Good"
    if score >= 55: return "C  ★★★☆☆  Average"
    if score >= 40: return "D  ★★☆☆☆  Needs Work"
    return            "F  ★☆☆☆☆  Poor – Overhaul Needed"


def print_report(contact: dict, skills: dict, education: list,
                 experience: dict, sections: dict,
                 score: dict, suggestions: list, raw_text: str):
    """Pretty-print the full analysis to the terminal."""

    os.system("cls" if os.name == "nt" else "clear")   # clear screen

    print()
    print("╔" + "═" * (WIDTH - 2) + "╗")
    print("║" + "  🤖  AI RESUME ANALYZER".center(WIDTH - 2) + "║")
    print("╚" + "═" * (WIDTH - 2) + "╝")

    # ── Contact ──────────────────────────────────────────────────────────────
    section_title("CONTACT INFORMATION")
    print(f"  📧  Email    : {contact.get('email',    'Not found')}")
    print(f"  📱  Phone    : {contact.get('phone',    'Not found')}")
    print(f"  🔗  LinkedIn : {contact.get('linkedin', 'Not found')}")
    print(f"  💻  GitHub   : {contact.get('github',   'Not found')}")

    # ── Skills ───────────────────────────────────────────────────────────────
    section_title("SKILLS DETECTED")
    tech = skills["tech"]
    soft = skills["soft"]
    verbs = skills["action_verbs"]

    if tech:
        # Print 4 per row
        chunks = [tech[i:i+4] for i in range(0, len(tech), 4)]
        print("  🛠  Tech Skills:")
        for chunk in chunks:
            print("       " + "  •  ".join(chunk))
    else:
        print("  🛠  Tech Skills : ❌  None detected")

    print()
    if soft:
        print(f"  🤝  Soft Skills : {', '.join(soft)}")
    else:
        print("  🤝  Soft Skills : ❌  None detected")

    print()
    if verbs:
        print(f"  💬  Action Verbs: {', '.join(verbs)}")
    else:
        print("  💬  Action Verbs: ❌  None detected")

    # ── Education ────────────────────────────────────────────────────────────
    section_title("EDUCATION")
    if education:
        for i, line in enumerate(education, 1):
            # Wrap long lines
            if len(line) > WIDTH - 6:
                line = line[:WIDTH - 9] + "…"
            print(f"  {i}. {line}")
    else:
        print("  ❌  No education details found.")

    # ── Experience ───────────────────────────────────────────────────────────
    section_title("EXPERIENCE")
    yrs = experience["estimated_years"]
    dr  = experience["date_ranges_found"]
    print(f"  ⏱  Estimated Experience : {yrs} year(s)")
    print(f"  📆  Date Ranges Found   : {dr}")

    # ── Sections checklist ───────────────────────────────────────────────────
    section_title("SECTIONS CHECKLIST")
    for sec, present in sections.items():
        mark = "✅" if present else "❌"
        print(f"  {mark}  {sec.title()}")

    # ── Score ────────────────────────────────────────────────────────────────
    header("  📊  RESUME SCORE")
    total = score["total"]
    print(f"\n  {score_bar(total)}")
    print(f"\n  Grade : {grade(total)}")
    print()
    print("  Score Breakdown:")
    for cat, pts in score["breakdown"].items():
        bar_len = int(pts / 30 * 20) if cat == "skills" else int(pts / 25 * 20)
        print(f"    {cat.replace('_',' ').title():<15} {pts:>3} pts")

    # ── Suggestions ──────────────────────────────────────────────────────────
    header("  💡  IMPROVEMENT SUGGESTIONS")
    for tip in suggestions:
        print(f"\n  {tip}")

    print()
    divider("═")
    print(f"  Analysis complete  ·  {datetime.now().strftime('%d %b %Y  %H:%M')}")
    divider("═")
    print()


# ─────────────────────────────────────────────────────────────────────────────
#  SAVE TO FILE
# ─────────────────────────────────────────────────────────────────────────────

def save_report(output_path: str, contact: dict, skills: dict,
                education: list, experience: dict, sections: dict,
                score: dict, suggestions: list):
    """Serialise the full analysis to a JSON file."""
    report = {
        "generated_at": datetime.now().isoformat(),
        "contact":      contact,
        "skills":       skills,
        "education":    education,
        "experience":   experience,
        "sections":     sections,
        "score":        score,
        "suggestions":  suggestions,
    }
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(f"\n  💾  Report saved → {output_path}\n")


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="🤖  AI Resume Analyzer – CLI Edition",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "resume",
        help="Path to your resume file  (.pdf  or  .txt)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="(Optional) Save JSON report to this path\n"
             "Example:  -o my_report.json",
    )
    args = parser.parse_args()

    # ── 1. Load text ─────────────────────────────────────────────────────────
    print(f"\n  ⏳  Loading resume: {args.resume} …")
    raw_text = load_resume(args.resume)
    text_lower = clean_text(raw_text)

    # ── 2. Contact info ──────────────────────────────────────────────────────
    contact = {
        "email":    extract_email(raw_text),
        "phone":    extract_phone(raw_text),
        "linkedin": extract_linkedin(raw_text),
        "github":   extract_github(raw_text),
    }

    # ── 3. NLP analysis ──────────────────────────────────────────────────────
    print("  ⏳  Running NLP analysis …")
    skills     = extract_skills(text_lower)
    education  = extract_education(raw_text)
    experience = extract_experience(raw_text)
    sections   = detect_sections(text_lower)

    # ── 4. Score & suggestions ───────────────────────────────────────────────
    score       = calculate_score(skills, sections, experience, text_lower)
    suggestions = generate_suggestions(skills, sections, score, experience)

    # ── 5. Display ───────────────────────────────────────────────────────────
    print_report(contact, skills, education, experience,
                 sections, score, suggestions, raw_text)

    # ── 6. Optional save ─────────────────────────────────────────────────────
    if args.output:
        save_report(args.output, contact, skills, education,
                    experience, sections, score, suggestions)


if __name__ == "__main__":
    main()
