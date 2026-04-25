"""
╔══════════════════════════════════════════════════════╗
║           ATS RESUME ANALYZER — CLI TOOL            ║
║     Match Your Resume Against Any Job Description   ║
╚══════════════════════════════════════════════════════╝

How to run:
    python ats_analyzer.py resume.pdf
    python ats_analyzer.py resume.txt
    python ats_analyzer.py resume.pdf -o result.json
"""

import os
import re
import sys
import json
import argparse
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
#  PDF EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

try:
    from pdfminer.high_level import extract_text as pdf_extract
except ImportError:
    pdf_extract = None


def load_resume(path: str) -> str:
    """Load resume from PDF or TXT file."""
    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        if pdf_extract is None:
            print("❌  pdfminer.six not installed. Run: pip install pdfminer.six")
            sys.exit(1)
        try:
            text = pdf_extract(path)
            if not text or not text.strip():
                print("⚠️  PDF appears to be scanned/image-based. Try a text-based PDF.")
                sys.exit(1)
            return text
        except Exception as e:
            print(f"❌  Could not read PDF: {e}")
            sys.exit(1)

    elif ext in (".txt", ".text"):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            print(f"❌  Could not read file: {e}")
            sys.exit(1)
    else:
        print(f"❌  Unsupported format '{ext}'. Use .pdf or .txt")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
#  GET JOB DESCRIPTION FROM TERMINAL
# ─────────────────────────────────────────────────────────────────────────────

def get_job_description() -> str:
    """
    Ask user to paste JD in terminal.
    They press Enter twice to finish.
    """
    print()
    print("─" * 60)
    print("  📋  PASTE YOUR JOB DESCRIPTION BELOW")
    print("  (Press ENTER twice when done)")
    print("─" * 60)
    print()

    lines = []
    empty_count = 0

    while True:
        try:
            line = input()
        except EOFError:
            break

        if line.strip() == "":
            empty_count += 1
            if empty_count >= 2:
                break
        else:
            empty_count = 0
            lines.append(line)

    jd = "\n".join(lines).strip()

    if not jd:
        print("❌  No job description entered. Please try again.")
        sys.exit(1)

    return jd


# ─────────────────────────────────────────────────────────────────────────────
#  TEXT HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def clean(text: str) -> str:
    """Lowercase and normalize whitespace."""
    return re.sub(r"\s+", " ", text.lower()).strip()


def extract_keywords(text: str) -> set:
    """
    Extract meaningful keywords from text.
    - Removes stopwords
    - Keeps single words AND important 2-word phrases
    """
    stopwords = {
        "a","an","the","and","or","but","in","on","at","to","for","of","with",
        "by","from","is","are","was","were","be","been","have","has","had",
        "do","does","did","will","would","could","should","may","might","can",
        "we","our","you","your","they","their","this","that","these","those",
        "not","no","so","as","if","its","it","i","me","my","he","she","him",
        "her","us","all","any","both","each","few","more","most","other",
        "such","than","too","very","just","also","about","above","after",
        "before","between","into","through","during","including","without",
        "per","via","how","what","which","who","when","where","while",
        "although","because","since","unless","until","whether","within",
        "experience","years","year","work","working","strong","good","ability",
        "knowledge","understanding","using","use","used","well","must","need",
        "required","preferred","plus","bonus","nice","have","excellent",
        "role","position","team","company","job","candidate","looking",
        "responsible","responsibilities","requirements","qualifications",
        "opportunity","join","help","hands","across","make","build","ensure",
        "new","key","high","large","small","great","best","top","main",
        "following","various","different","multiple","related","based",
    }

    text_lower = clean(text)

    # --- Single word keywords ---
    words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9+#.]*\b", text_lower)
    single = {w for w in words if w not in stopwords and len(w) > 2}

    # --- Two-word tech phrases (very important for ATS) ---
    two_word_patterns = [
        # Languages & tools
        r"machine learning", r"deep learning", r"natural language processing",
        r"computer vision", r"data science", r"data analysis", r"data engineering",
        r"software development", r"software engineering", r"web development",
        r"full stack", r"front end", r"back end", r"rest api", r"restful api",
        r"api integration", r"ci/cd", r"object oriented", r"test driven",
        r"agile methodology", r"scrum methodology", r"version control",
        r"cloud computing", r"microservices architecture", r"system design",
        r"problem solving", r"critical thinking", r"time management",
        r"team collaboration", r"project management", r"communication skills",
        r"manual testing", r"automated testing", r"test cases", r"bug reporting",
        r"regression testing", r"unit testing", r"integration testing",
        r"react js", r"node js", r"next js", r"vue js", r"angular js",
        r"power bi", r"tableau", r"microsoft excel", r"microsoft office",
        r"git github", r"aws azure", r"google cloud",
    ]

    two_word = set()
    for pattern in two_word_patterns:
        if pattern in text_lower:
            two_word.add(pattern)

    # Also extract any consecutive non-stopword pairs
    word_list = [w for w in words if w not in stopwords and len(w) > 2]
    for i in range(len(word_list) - 1):
        phrase = f"{word_list[i]} {word_list[i+1]}"
        two_word.add(phrase)

    return single | two_word


# ─────────────────────────────────────────────────────────────────────────────
#  ATS MATCHING ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def extract_jd_requirements(jd_text: str) -> dict:
    """
    Extract structured requirements from JD:
    - Required skills/keywords
    - Experience years required
    - Education requirements
    - Soft skills mentioned
    """
    jd_lower = clean(jd_text)

    # All keywords from JD
    all_keywords = extract_keywords(jd_text)

    # Experience years required
    exp_match = re.search(
        r"(\d+)\+?\s*(?:to\s*\d+)?\s*years?\s*(?:of\s*)?(?:experience|exp)",
        jd_lower
    )
    required_exp = int(exp_match.group(1)) if exp_match else 0

    # Education requirement
    edu_keywords = ["bachelor", "master", "phd", "b.tech", "m.tech", "degree",
                    "b.sc", "m.sc", "mba", "graduate", "undergraduate"]
    required_edu = [e for e in edu_keywords if e in jd_lower]

    # Important tech skills mentioned in JD
    tech_skills = [
        "python", "java", "javascript", "typescript", "c++", "c#", "ruby",
        "go", "rust", "swift", "kotlin", "php", "scala", "r", "matlab",
        "html", "css", "react", "angular", "vue", "nodejs", "django", "flask",
        "fastapi", "spring", "express", "graphql", "sql", "mysql", "postgresql",
        "mongodb", "redis", "elasticsearch", "firebase", "sqlite", "oracle",
        "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "terraform",
        "ansible", "linux", "bash", "git", "github", "gitlab",
        "machine learning", "deep learning", "nlp", "tensorflow", "pytorch",
        "keras", "scikit", "pandas", "numpy", "tableau", "power bi",
        "agile", "scrum", "jira", "figma", "selenium", "postman",
        "rest", "api", "microservices", "ci/cd", "devops", "testing",
        "manual testing", "automation", "dsa", "data structures", "algorithms",
        "oops", "oop", "system design", "networking", "tcp", "http",
    ]
    jd_tech = [s for s in tech_skills if s in jd_lower]

    # Soft skills in JD
    soft_skills = [
        "communication", "leadership", "teamwork", "collaboration",
        "problem solving", "analytical", "critical thinking", "adaptability",
        "time management", "attention to detail", "self motivated",
        "fast learner", "quick learner", "multitasking",
    ]
    jd_soft = [s for s in soft_skills if s in jd_lower]

    return {
        "all_keywords": all_keywords,
        "tech_skills":  jd_tech,
        "soft_skills":  jd_soft,
        "required_exp": required_exp,
        "required_edu": required_edu,
    }


def calculate_ats_score(resume_text: str, jd: dict) -> dict:
    """
    Calculate ATS match score out of 100.

    Category              Max   Logic
    ──────────────────────────────────────────────────
    Keyword Match          50   % of JD keywords in resume
    Tech Skills Match      25   % of JD tech skills in resume
    Soft Skills Match      10   Soft skill overlap
    Experience Match       10   Resume exp >= JD required
    Education Match         5   Degree mentioned
    ──────────────────────────────────────────────────
    """
    resume_lower = clean(resume_text)
    resume_keywords = extract_keywords(resume_text)
    breakdown = {}

    # 1. Overall Keyword Match (50 pts)
    jd_keywords = jd["all_keywords"]
    if jd_keywords:
        matched = {k for k in jd_keywords if k in resume_lower}
        keyword_score = min(len(matched) / max(len(jd_keywords), 1) * 50, 50)
    else:
        matched = set()
        keyword_score = 0
    breakdown["keyword_match"] = round(keyword_score)

    # 2. Tech Skills Match (25 pts)
    jd_tech = jd["tech_skills"]
    if jd_tech:
        tech_matched = [s for s in jd_tech if s in resume_lower]
        tech_score = min(len(tech_matched) / max(len(jd_tech), 1) * 25, 25)
    else:
        tech_matched = []
        tech_score = 25  # no specific tech required = full marks
    breakdown["tech_skills"] = round(tech_score)

    # 3. Soft Skills Match (10 pts)
    jd_soft = jd["soft_skills"]
    if jd_soft:
        soft_matched = [s for s in jd_soft if s in resume_lower]
        soft_score = min(len(soft_matched) / max(len(jd_soft), 1) * 10, 10)
    else:
        soft_matched = []
        soft_score = 10
    breakdown["soft_skills"] = round(soft_score)

    # 4. Experience Match (10 pts)
    req_exp = jd["required_exp"]
    exp_years_found = re.findall(r"(\d+\.?\d*)\s*\+?\s*years?", resume_lower)
    resume_exp = max([float(y) for y in exp_years_found], default=0)
    if req_exp == 0:
        exp_score = 10
    elif resume_exp >= req_exp:
        exp_score = 10
    elif resume_exp >= req_exp * 0.5:
        exp_score = 5
    else:
        exp_score = 2
    breakdown["experience"] = exp_score

    # 5. Education Match (5 pts)
    req_edu = jd["required_edu"]
    if not req_edu:
        edu_score = 5
    else:
        edu_found = any(e in resume_lower for e in req_edu)
        edu_score = 5 if edu_found else 0
    breakdown["education"] = edu_score

    total = sum(breakdown.values())

    # What's matched vs missing from JD tech skills
    missing_tech = [s for s in jd_tech if s not in resume_lower]
    matched_tech = [s for s in jd_tech if s in resume_lower]

    # Important JD keywords missing from resume
    important_missing = []
    for kw in jd_keywords:
        if kw not in resume_lower and len(kw) > 3 and " " not in kw:
            important_missing.append(kw)
    important_missing = sorted(important_missing)[:15]  # top 15

    return {
        "total":            min(total, 100),
        "breakdown":        breakdown,
        "matched_tech":     matched_tech,
        "missing_tech":     missing_tech,
        "missing_keywords": important_missing,
        "soft_matched":     soft_matched if jd_soft else [],
        "resume_exp":       resume_exp,
        "required_exp":     req_exp,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  SUGGESTIONS ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def generate_suggestions(result: dict, jd: dict) -> list:
    """Generate personalised, actionable ATS suggestions."""
    tips = []
    total = result["total"]

    # Missing tech skills
    if result["missing_tech"]:
        missing = ", ".join(result["missing_tech"][:6])
        tips.append(
            f"🛠️  Add these missing tech skills to your resume:\n"
            f"     → {missing}"
        )

    # Missing keywords
    if result["missing_keywords"]:
        kws = ", ".join(result["missing_keywords"][:8])
        tips.append(
            f"🔑  These JD keywords are missing from your resume:\n"
            f"     → {kws}\n"
            f"     Tip: Use exact words from the JD — ATS matches keywords!"
        )

    # Experience gap
    req = result["required_exp"]
    got = result["resume_exp"]
    if req > 0 and got < req:
        tips.append(
            f"📅  JD requires {req} years experience, "
            f"resume shows {got} years.\n"
            f"     Tip: Add internships, projects, freelance work to show more experience."
        )

    # Soft skills
    if jd["soft_skills"] and not result["soft_matched"]:
        soft = ", ".join(jd["soft_skills"][:4])
        tips.append(
            f"🤝  Add soft skills mentioned in JD:\n"
            f"     → {soft}"
        )

    # Score based advice
    if total >= 80:
        tips.append(
            "✅  Excellent ATS match! Your resume is well-aligned with this JD.\n"
            "     Tip: Tailor your summary section to mirror the JD language."
        )
    elif total >= 60:
        tips.append(
            "📈  Good match! Add the missing keywords above to push score higher.\n"
            "     Tip: Use exact phrases from JD in your skills and experience sections."
        )
    elif total >= 40:
        tips.append(
            "⚠️   Moderate match. Your resume needs more JD-specific keywords.\n"
            "     Tip: Rewrite your skills section using exact terms from the JD."
        )
    else:
        tips.append(
            "❌  Low ATS match. This JD may require skills not in your resume.\n"
            "     Tip: Only apply if you can genuinely add the missing skills, OR\n"
            "          target JDs that better match your current profile."
        )

    # General ATS tip
    tips.append(
        "💡  ATS Tip: Avoid tables, columns, images in resume — "
        "ATS systems cannot read them!"
    )

    return tips


# ─────────────────────────────────────────────────────────────────────────────
#  DISPLAY
# ─────────────────────────────────────────────────────────────────────────────

WIDTH = 62

def divider(char="─"):
    print(char * WIDTH)

def score_bar(score: int, max_score: int = 100) -> str:
    filled = int(score / max_score * 40)
    bar    = "█" * filled + "░" * (40 - filled)
    return f"[{bar}] {score}%"

def grade(score: int) -> tuple:
    if score >= 85: return "EXCELLENT MATCH", "🟢"
    if score >= 70: return "GOOD MATCH",      "🟡"
    if score >= 55: return "MODERATE MATCH",  "🟠"
    if score >= 40: return "WEAK MATCH",      "🔴"
    return                  "POOR MATCH",     "❌"


def print_report(result: dict, jd: dict, suggestions: list):
    """Print the full ATS report to terminal."""

    os.system("cls" if os.name == "nt" else "clear")

    print()
    print("╔" + "═" * (WIDTH - 2) + "╗")
    print("║" + "  🤖  ATS RESUME ANALYZER".center(WIDTH - 2) + "║")
    print("║" + "  Match Score Against Job Description".center(WIDTH - 2) + "║")
    print("╚" + "═" * (WIDTH - 2) + "╝")

    # ── ATS Score ────────────────────────────────────────────────────────────
    total = result["total"]
    label, emoji = grade(total)
    print()
    divider("═")
    print(f"  📊  ATS MATCH SCORE")
    divider("═")
    print()
    print(f"  {score_bar(total)}")
    print()
    print(f"  {emoji}  {label}  —  {total}/100")
    print()

    # ── Score Breakdown ───────────────────────────────────────────────────────
    print("  Score Breakdown:")
    divider()
    categories = {
        "keyword_match": ("Keyword Match",  50),
        "tech_skills":   ("Tech Skills",    25),
        "soft_skills":   ("Soft Skills",    10),
        "experience":    ("Experience",     10),
        "education":     ("Education",       5),
    }
    for key, (label, max_pts) in categories.items():
        got = result["breakdown"].get(key, 0)
        bar_filled = int(got / max_pts * 20)
        mini_bar = "█" * bar_filled + "░" * (20 - bar_filled)
        print(f"  {label:<18} [{mini_bar}] {got}/{max_pts}")

    # ── Tech Skills ───────────────────────────────────────────────────────────
    print()
    divider("═")
    print(f"  🛠️   TECH SKILLS ANALYSIS")
    divider("═")

    matched = result["matched_tech"]
    missing = result["missing_tech"]

    if matched:
        print()
        print("  ✅  Found in Resume:")
        chunks = [matched[i:i+4] for i in range(0, len(matched), 4)]
        for chunk in chunks:
            print("      " + "  •  ".join(chunk))

    if missing:
        print()
        print("  ❌  Missing from Resume (in JD):")
        chunks = [missing[i:i+4] for i in range(0, len(missing), 4)]
        for chunk in chunks:
            print("      " + "  •  ".join(chunk))

    if not matched and not missing:
        print()
        print("  ℹ️   No specific tech skills detected in JD.")

    # ── Keywords ──────────────────────────────────────────────────────────────
    if result["missing_keywords"]:
        print()
        divider("═")
        print(f"  🔑  MISSING KEYWORDS (Add These to Resume!)")
        divider("═")
        print()
        kws = result["missing_keywords"]
        chunks = [kws[i:i+4] for i in range(0, len(kws), 4)]
        for chunk in chunks:
            print("      " + "  |  ".join(chunk))

    # ── Experience ────────────────────────────────────────────────────────────
    print()
    divider("═")
    print(f"  📅  EXPERIENCE")
    divider("═")
    print()
    req = result["required_exp"]
    got = result["resume_exp"]
    print(f"  JD Requires  :  {req} year(s)" if req > 0 else "  JD Requires  :  Not specified")
    print(f"  Your Resume  :  {got} year(s)")
    if req > 0 and got >= req:
        print(f"  Status       :  ✅  You meet the experience requirement!")
    elif req > 0:
        print(f"  Status       :  ⚠️   {req - got:.1f} more year(s) needed")

    # ── Suggestions ───────────────────────────────────────────────────────────
    print()
    divider("═")
    print(f"  💡  IMPROVEMENT SUGGESTIONS")
    divider("═")
    for tip in suggestions:
        print()
        print(f"  {tip}")

    # ── Footer ────────────────────────────────────────────────────────────────
    print()
    divider("═")
    print(f"  Analysis done  ·  {datetime.now().strftime('%d %b %Y  %H:%M')}")
    divider("═")
    print()


# ─────────────────────────────────────────────────────────────────────────────
#  SAVE REPORT
# ─────────────────────────────────────────────────────────────────────────────

def save_report(path: str, result: dict, suggestions: list):
    report = {
        "generated_at":    datetime.now().isoformat(),
        "ats_score":       result["total"],
        "breakdown":       result["breakdown"],
        "matched_tech":    result["matched_tech"],
        "missing_tech":    result["missing_tech"],
        "missing_keywords":result["missing_keywords"],
        "experience": {
            "required": result["required_exp"],
            "found":    result["resume_exp"],
        },
        "suggestions": suggestions,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\n  💾  Report saved → {path}\n")


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="🤖  ATS Resume Analyzer — Match resume against Job Description",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "resume",
        help="Path to resume file (.pdf or .txt)\nExample: resume.pdf",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="(Optional) Save JSON report\nExample: -o result.json",
    )
    args = parser.parse_args()

    # 1. Load Resume
    print(f"\n  ⏳  Loading resume: {args.resume} …")
    resume_text = load_resume(args.resume)
    print(f"  ✅  Resume loaded! ({len(resume_text.split())} words)")

    # 2. Get JD from terminal
    jd_text = get_job_description()
    print(f"\n  ✅  JD received! ({len(jd_text.split())} words)")
    print("  ⏳  Analyzing match …")

    # 3. Extract JD requirements
    jd = extract_jd_requirements(jd_text)

    # 4. Calculate ATS Score
    result = calculate_ats_score(resume_text, jd)

    # 5. Generate Suggestions
    suggestions = generate_suggestions(result, jd)

    # 6. Print Report
    print_report(result, jd, suggestions)

    # 7. Save if requested
    if args.output:
        save_report(args.output, result, suggestions)


if __name__ == "__main__":
    main()
