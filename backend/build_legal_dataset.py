import os
import io
import json
import re
import time
import math
import requests
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
from datetime import datetime

try:
    from groq import Groq
except ImportError:
    Groq = None

# ============================================================
# CONFIG
# ============================================================

# Configure Groq LLM (Set your API Key here or in environment)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
USE_LLM = False
groq_client = None

if Groq and GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
    USE_LLM = True
    print("[INFO] LLM (Groq Llama 3.3 70B) is ENABLED for data extraction.")
else:
    print("[WARN] LLM parsing disabled. Please set GROQ_API_KEY and `pip install groq`.")


START_YEAR = 1950
END_YEAR = 2025
MIN_EACH = 10_000  # Target cases per category (civil + criminal + traffic)

OUTPUT_FILE = "cases_ipc_crime_verdict.json"   # Single output file

# Public AWS Open Data — Indian Supreme Court Judgments
METADATA_URL = (
    "https://indian-supreme-court-judgments.s3.amazonaws.com/"
    "metadata/parquet/year={year}/metadata.parquet"
)

# ============================================================
# KEYWORD CLASSIFIERS
# ============================================================

CRIMINAL_KEYWORDS = [
    "murder",
    "homicide",
    "culpable homicide",
    "rape",
    "sexual assault",
    "molestation",
    "pocso",
    "kidnapping",
    "abduction",
    "robbery",
    "dacoity",
    "theft",
    "burglary",
    "assault",
    "hurt",
    "grievous hurt",
    "cheating",
    "fraud",
    "forgery",
    "ndps",
    "narcotic drugs",
    "psychotropic",
    "bail",
    "custody",
    "remand",
    "sentence",
    "convicted",
    "acquitted",
    "protection of children from sexual offences",
    "dowry death",
    "cruelty",
    "498a",
    "304b",
    "extortion",
    "intimidation",
    "counterfeiting",
    "human trafficking",
    "acid attack",
]

TRAFFIC_KEYWORDS = [
    "motor vehicles act",
    "motor vehicle act",
    "mv act",
    "m.v. act",
    "m v act",
    "m.v.act",
    "mvact",
    "motor vehicles act, 1988",
    "motor vehicles act 1988",
    "mva",
    "m.v.a.",
    "road accident",
    "motor accident",
    "traffic accident",
    "rash and negligent driving",
    "rash driving",
    "driving licence",
    "driving license",
    "learner's licence",
    "regional transport",
    "transport authority",
    "hit and run",
    "hit-and-run",
    "motor accident claims tribunal",
    "mact",
    "304a",
    "negligent driving",
    "vehicle accident",
    "compensation tribunal",
    "third party insurance",
]

CIVIL_KEYWORDS = [
    "contract",
    "specific performance",
    "property",
    "ownership",
    "title",
    "possession",
    "land acquisition",
    "compensation",
    "service matter",
    "employment",
    "dismissal from service",
    "matrimonial",
    "divorce",
    "maintenance",
    "alimony",
    "custody of child",
    "guardianship",
    "arbitration",
    "commercial dispute",
    "tax",
    "income tax",
    "gst",
    "excise",
    "customs",
    "company law",
    "insolvency",
    "bankruptcy",
    "ibc",
    "writ petition",
    "mandamus",
    "certiorari",
    "habeas corpus",
    "civil suit",
    "injunction",
    "declaration",
    "succession",
    "probate",
    "will",
    "partition",
    "rent",
    "tenancy",
    "eviction",
    "consumer",
    "deficiency of service",
]

# ============================================================
# IPC SECTION MAP
# ============================================================

IPC_OFFENSE_MAP = {
    "34": ("Common Intention", "Common Intention"),
    "107": ("Abetment", "Abetment"),
    "120A": ("Criminal Conspiracy (Definition)", "Conspiracy"),
    "120B": ("Criminal Conspiracy", "Conspiracy"),
    "147": ("Rioting", "Violent Crime"),
    "148": ("Rioting with Deadly Weapon", "Violent Crime"),
    "149": ("Unlawful Assembly", "Unlawful Assembly"),
    "201": ("Causing Disappearance of Evidence", "Obstruction of Justice"),
    "279": ("Rash Driving on Public Way", "Traffic Offence"),
    "302": ("Murder", "Violent Crime"),
    "303": ("Murder by Life Convict", "Violent Crime"),
    "304": ("Culpable Homicide Not Amounting to Murder", "Violent Crime"),
    "304A": ("Causing Death by Negligence", "Traffic Offence"),
    "304B": ("Dowry Death", "Domestic Violence"),
    "305": ("Abetment of Suicide of Child", "Violent Crime"),
    "306": ("Abetment of Suicide", "Violent Crime"),
    "307": ("Attempt to Murder", "Violent Crime"),
    "308": ("Attempt Culpable Homicide", "Violent Crime"),
    "323": ("Voluntarily Causing Hurt", "Violent Crime"),
    "324": ("Hurt by Dangerous Weapons", "Violent Crime"),
    "325": ("Grievous Hurt", "Violent Crime"),
    "326": ("Grievous Hurt by Dangerous Weapons", "Violent Crime"),
    "326A": ("Acid Attack", "Violent Crime"),
    "326B": ("Attempt Acid Attack", "Violent Crime"),
    "337": ("Causing Hurt by Rash Act", "Traffic Offence"),
    "338": ("Causing Grievous Hurt by Rash Act", "Traffic Offence"),
    "354": ("Assault on Woman", "Sexual Offence"),
    "354A": ("Sexual Harassment", "Sexual Offence"),
    "354B": ("Disrobing", "Sexual Offence"),
    "354C": ("Voyeurism", "Sexual Offence"),
    "354D": ("Stalking", "Sexual Offence"),
    "363": ("Kidnapping", "Violent Crime"),
    "364": ("Kidnapping for Murder", "Violent Crime"),
    "364A": ("Kidnapping for Ransom", "Violent Crime"),
    "365": ("Abduction", "Violent Crime"),
    "366": ("Kidnapping Woman for Marriage", "Violent Crime"),
    "370": ("Human Trafficking", "Violent Crime"),
    "370A": ("Trafficking of Minor", "Violent Crime"),
    "375": ("Rape (Definition)", "Sexual Offence"),
    "376": ("Rape", "Sexual Offence"),
    "376A": ("Rape Causing Death", "Sexual Offence"),
    "376D": ("Gang Rape", "Sexual Offence"),
    "379": ("Theft", "Property Crime"),
    "380": ("Theft in Dwelling House", "Property Crime"),
    "381": ("Theft by Employee", "Property Crime"),
    "382": ("Theft with Preparation to Hurt", "Property Crime"),
    "383": ("Extortion", "Property Crime"),
    "384": ("Extortion by Threat", "Property Crime"),
    "385": ("Extortion with Fear", "Property Crime"),
    "386": ("Extortion by Death Threat", "Property Crime"),
    "392": ("Robbery", "Property Crime"),
    "393": ("Attempt to Commit Robbery", "Property Crime"),
    "394": ("Robbery with Hurt", "Property Crime"),
    "395": ("Dacoity", "Property Crime"),
    "396": ("Dacoity with Murder", "Property Crime"),
    "397": ("Robbery or Dacoity with Deadly Weapon", "Property Crime"),
    "405": ("Criminal Breach of Trust (Definition)", "Economic Offence"),
    "406": ("Criminal Breach of Trust", "Economic Offence"),
    "407": ("Breach of Trust by Carrier", "Economic Offence"),
    "408": ("Breach of Trust by Employee", "Economic Offence"),
    "409": ("Breach of Trust by Public Servant", "Economic Offence"),
    "411": ("Dishonestly Receiving Stolen Property", "Property Crime"),
    "415": ("Cheating (Definition)", "Economic Offence"),
    "416": ("Cheating by Personation", "Economic Offence"),
    "419": ("Cheating by Impersonation", "Economic Offence"),
    "420": ("Cheating and Dishonest Delivery of Property", "Economic Offence"),
    "427": ("Mischief Causing Damage", "Property Crime"),
    "435": ("Mischief by Fire", "Property Crime"),
    "436": ("Mischief by Fire to Dwelling", "Property Crime"),
    "441": ("Criminal Trespass", "Property Crime"),
    "457": ("Lurking House Trespass", "Property Crime"),
    "458": ("Lurking House Trespass with Hurt", "Property Crime"),
    "463": ("Forgery (Definition)", "Economic Offence"),
    "465": ("Punishment for Forgery", "Economic Offence"),
    "467": ("Forgery of Valuable Security", "Economic Offence"),
    "468": ("Forgery for Cheating", "Economic Offence"),
    "471": ("Using Forged Documents as Genuine", "Economic Offence"),
    "489A": ("Counterfeiting Currency Notes", "Economic Offence"),
    "489B": ("Selling Counterfeit Currency", "Economic Offence"),
    "489C": ("Possession of Counterfeit Currency", "Economic Offence"),
    "489D": ("Making Instruments for Counterfeiting", "Economic Offence"),
    "493": ("Cohabitation by Deceit", "Domestic Violence"),
    "494": ("Bigamy", "Domestic Violence"),
    "498A": ("Cruelty by Husband or Relatives", "Domestic Violence"),
    "499": ("Defamation", "Other"),
    "500": ("Punishment for Defamation", "Other"),
    "504": ("Intentional Insult", "Other"),
    "505": ("Statements Causing Public Mischief", "Other"),
    "506": ("Criminal Intimidation", "Other"),
    "509": ("Insulting Modesty of Woman", "Sexual Offence"),
}

KEYWORD_TO_IPC = {
    "murder": "302",
    "culpable homicide": "304",
    "rape": "376",
    "kidnapping": "363",
    "abduction": "365",
    "dacoity": "395",
    "robbery": "392",
    "theft": "379",
    "hurt": "323",
    "grievous hurt": "325",
    "cheating": "420",
    "fraud": "420",
    "forgery": "463",
    "dowry death": "304B",
    "cruelty": "498A",
    "extortion": "383",
    "intimidation": "506",
    "counterfeiting": "489A",
    "human trafficking": "370",
    "acid attack": "326A",
    "rash driving": "279",
    "negligent driving": "304A",
}

# ============================================================
# HELPERS
# ============================================================


def fetch_parquet(year: int) -> pd.DataFrame | None:
    url = METADATA_URL.format(year=year)
    print(f"\n[FETCH] year={year} -> {url}")
    try:
        resp = requests.get(url, timeout=60)
    except Exception as e:
        print(f"[WARN] Request error for {year}: {e}")
        return None
    if resp.status_code != 200:
        print(f"[WARN] HTTP {resp.status_code} for year {year}")
        return None
    try:
        df = pd.read_parquet(io.BytesIO(resp.content))
        print(f"[OK]   {len(df)} records loaded for {year}")
        return df
    except Exception as e:
        print(f"[ERR]  Parquet read failed for {year}: {e}")
        return None


def html_to_text(html: str) -> str:
    """Strip HTML tags and return plain text."""
    if not isinstance(html, str) or not html.strip():
        return ""
    return BeautifulSoup(html, "html.parser").get_text(separator="\n", strip=True)


def contains_any(text: str, keywords: list) -> bool:
    if not isinstance(text, str):
        return False
    t = text.lower()
    return any(k.lower() in t for k in keywords)


def sanitize(v):
    """Convert any value to a JSON-safe type."""
    if isinstance(v, (list, dict)):
        return v
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(v, pd.Timestamp):
        return v.isoformat()
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


# ============================================================
# IPC EXTRACTION  ->  structured list of dicts
# ============================================================


def extract_ipc_sections(text: str) -> list:
    """
    Extract IPC sections from judgment text.
    Returns:
        [
          {
            "section":          "Section 302 IPC",
            "section_number":   "302",
            "offense_name":     "Murder",
            "offense_category": "Violent Crime",
            "is_primary":       True   # highest-priority section
          },
          ...
        ]
    """
    if not isinstance(text, str):
        return []

    t = text.replace("Indian Penal Code", "IPC").replace("Penal Code", "IPC")

    patterns = [
        r"(?:Section|Sec\.?|s\.?|u/s|u/ss)\.?\s*([\d\w\s,/\(\)]+?)\s+(?:of\s+(?:the\s+)?)?IPC",
        r"IPC\s+(?:Section|Sec\.?|s\.?)\s*([\d\w\s,/\(\)]+)",
        r"under\s+(?:Section|Sec\.?|s\.?)\s*([\d\w\s,/\(\)]+?)\s+(?:of\s+(?:the\s+)?)?IPC",
    ]

    raw: set = set()
    for pat in patterns:
        for m in re.findall(pat, t, re.IGNORECASE | re.DOTALL):
            for s in re.split(r"[,/]| and | read with ", m):
                s = s.strip()
                if re.match(r"^\d+[A-Za-z0-9\(\)]*$", s):
                    raw.add(s)

    if not raw:
        # Fallback to inference from keywords
        t_low = text.lower()
        for kw, sec in KEYWORD_TO_IPC.items():
            if re.search(r"\b" + re.escape(kw) + r"\b", t_low):
                raw.add(sec)

    if not raw:
        return []

    # Priority order for choosing the "primary" section
    PRIORITY = [
        "302",
        "376",
        "376A",
        "376D",
        "395",
        "396",
        "420",
        "304B",
        "307",
        "364A",
        "370",
        "489A",
        "326A",
        "498A",
        "304",
        "363",
        "392",
        "406",
        "467",
        "147",
        "120B",
        "306",
        "379",
        "499",
        "506",
    ]
    primary = None
    for p in PRIORITY:
        if p in raw:
            primary = p
            break
    if primary is None:
        primary = sorted(raw)[0]

    result = []
    for sec in sorted(raw):
        name, cat = IPC_OFFENSE_MAP.get(sec, ("Unknown Provision", "Other"))
        result.append(
            {
                "section": f"Section {sec} IPC",
                "section_number": sec,
                "offense_name": name,
                "offense_category": cat,
                "is_primary": sec == primary,
            }
        )
    return result


# ============================================================
# CRIME DETAILS  ->  clean plain-text summary
# ============================================================


def extract_crime_details(text: str, meta_text: str) -> str:
    """
    Return a clean, concise crime description from the judgment text.
    Tries to pull the most informative sentences. Falls back to
    metadata description if full text is unavailable.
    """
    # Prefer full text; fall back to metadata
    source = text.strip() if text and len(text) > 200 else meta_text.strip()
    if not source:
        return "Crime details not available."

    # Split into sentences
    sentences = re.split(r"(?<=[.!?])\s+", source)

    # Score each sentence by relevance keywords
    RELEVANT = [
        "accused",
        "victim",
        "deceased",
        "complainant",
        "murder",
        "rape",
        "robbery",
        "dacoity",
        "kidnap",
        "assault",
        "hurt",
        "cheating",
        "fraud",
        "forgery",
        "convicted",
        "acquitted",
        "offence",
        "crime",
        "fir",
        "arrest",
        "chargesheet",
        "prosecution",
        "section",
        "ipc",
        "sentence",
        "bail",
        "evidence",
        "witness",
        "court",
        "held",
    ]

    scored = []
    for s in sentences:
        s = s.strip()
        if len(s) < 30:
            continue
        score = sum(1 for kw in RELEVANT if kw.lower() in s.lower())
        scored.append((score, s))

    # Pick top 4 most relevant sentences
    scored.sort(key=lambda x: -x[0])
    top = [s for _, s in scored[:4]]

    if not top:
        return source[:500]

    return " ".join(top)[:1000]


# ============================================================
# VERDICT EXTRACTION  ->  structured dict
# ============================================================


def extract_verdict(text: str, disposal_raw: str) -> dict:
    """
    Returns:
        {
          "outcome":          "Convicted" | "Acquitted" | ...,
          "disposal_nature":  raw disposal string from metadata,
          "sentence":         "Life Imprisonment" | "10 Years RI" | None,
          "fine_inr":         50000 | None,
          "compensation_inr": 100000 | None,
          "detail":           human-readable summary of verdict
        }
    """
    t = (text or "").lower()
    disposal_raw = str(disposal_raw or "").strip()

    # ── Outcome ────────────────────────────────────────────────
    outcome = "Unknown"
    if any(w in t for w in ["acquitted", "acquittal", "not guilty"]):
        outcome = "Acquitted"
    elif "death sentence" in t and any(w in t for w in ["commuted", "reduced"]):
        outcome = "Death Sentence Commuted to Life Imprisonment"
    elif "death sentence" in t or "capital punishment" in t:
        outcome = "Death Sentence Confirmed"
    elif any(w in t for w in ["convicted", "conviction", "found guilty"]):
        if "modified" in t or "reduced" in t or "partly" in t:
            outcome = "Convicted — Sentence Modified"
        else:
            outcome = "Convicted"
    elif "remanded" in t or "fresh trial" in t:
        outcome = "Remanded for Fresh Trial"
    elif "appeal" in t and any(w in t for w in ["allowed", "accepted"]):
        outcome = "Appeal Allowed"
    elif "appeal" in t and "dismissed" in t:
        outcome = "Appeal Dismissed"
    elif "slp dismissed" in t:
        outcome = "SLP Dismissed"
    elif "bail" in t and "granted" in t:
        outcome = "Bail Granted"

    # Use disposal_raw as fallback
    if outcome == "Unknown" and disposal_raw:
        outcome = disposal_raw

    # ── Sentence ───────────────────────────────────────────────
    sentence = None
    if "life imprisonment" in t:
        sentence = "Life Imprisonment"
    else:
        m = re.search(
            r"(\d+)\s*years?\s*(?:rigorous|simple|r\.i\.|s\.i\.)?[\s\w]*imprisonment", t
        )
        if m:
            yrs = int(m.group(1))
            kind = "Rigorous" if "rigorous" in t else "Simple"
            sentence = f"{yrs} Years {kind} Imprisonment"
        elif "imprisonment" in t:
            sentence = "Imprisonment (duration not specified)"

    # ── Fine ────────────────────────────────────────────────────
    fine_inr = None
    fm = re.search(r"fine\s+of\s+(?:rs\.?|rupees?|inr)\.?\s*([\d,]+)", t)
    if fm:
        try:
            fine_inr = int(fm.group(1).replace(",", ""))
        except ValueError:
            pass

    # ── Compensation ────────────────────────────────────────────
    comp_inr = None
    cm = re.search(r"compensation\s+of\s+(?:rs\.?|rupees?|inr)\.?\s*([\d,]+)", t)
    if cm:
        try:
            comp_inr = int(cm.group(1).replace(",", ""))
        except ValueError:
            pass

    # ── Detail sentence ─────────────────────────────────────────
    detail_parts = []
    if outcome:
        detail_parts.append(f"Outcome: {outcome}.")
    if sentence:
        detail_parts.append(f"Sentence: {sentence}.")
    if fine_inr:
        detail_parts.append(f"Fine: Rs.{fine_inr:,}.")
    if comp_inr:
        detail_parts.append(f"Compensation to victim: Rs.{comp_inr:,}.")
    if disposal_raw and disposal_raw not in outcome:
        detail_parts.append(f"Disposal: {disposal_raw}.")
    detail = " ".join(detail_parts) if detail_parts else "See full judgment."

    return {
        "outcome": outcome,
        "disposal_nature": disposal_raw if disposal_raw else "Not Applicable",
        "sentence": sentence if sentence else "Not Applicable",
        "fine_inr": fine_inr if fine_inr is not None else 0,
        "compensation_inr": comp_inr if comp_inr is not None else 0,
        "detail": detail,
    }


def extract_crime_keywords(text: str) -> list:
    """Extract all relevant crime/traffic/civil keywords found in the text."""
    if not isinstance(text, str):
        return []

    t = text.lower()
    found = set()
    all_kws = CRIMINAL_KEYWORDS + TRAFFIC_KEYWORDS + CIVIL_KEYWORDS
    for kw in all_kws:
        if re.search(r"\b" + re.escape(kw.lower()) + r"\b", t):
            found.add(kw)
    return sorted(list(found))


# ============================================================
# LLM EXTRACTION
# ============================================================

def extract_with_llm(text: str, category_guess: str) -> dict:
    """Uses Groq Llama 3.3 70B to robustly extract case information and infer missing details."""
    if not USE_LLM or not groq_client:
        return {}

    text_snippet = text[:25000]
    prompt = f"""You are an advanced legal dataset builder. Analyze the following Indian Supreme Court judgment.
Extract the relevant details accurately. Use your broad legal knowledge to infer information if contextually obvious.
Respond ONLY with a valid JSON strictly matching the schema below:

{{
    "ipc_section": [
        {{
            "section": "E.g. Section 302 IPC",
            "section_number": "E.g. 302",
            "offense_name": "E.g. Murder",
            "offense_category": "E.g. Violent Crime, Economic Offence, Traffic Offence",
            "is_primary": true or false
        }}
    ],
    "crime_keywords": ["List of identified legal/crime-related keywords"],
    "crime_details": "A detailed, plain-text narrative summarizing the facts of the crime, dispute, or accident (max 3 sentences)",
    "verdict": {{
        "outcome": "Brief outcome description (e.g. Convicted, Acquitted, Appeal Dismissed)",
        "disposal_nature": "Nature of disposal if mentioned, else 'Not Applicable'",
        "sentence": "Sentence details if applicable, else 'Not Applicable'",
        "fine_inr": "integer fine amount if applicable, else 0. Do NOT use null.",
        "compensation_inr": "integer compensation amount if applicable, else 0. Do NOT use null.",
        "detail": "Detailed summary of the verdict"
    }}
}}

Likely Category context: {category_guess}
Judgment Text snippet:
{text_snippet}
"""
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        res_text = response.choices[0].message.content.strip()
        
        return json.loads(res_text)
    except Exception as e:
        print(f"\n[LLM_ERROR] Parsing failed: {e}")
        return {}


# ============================================================
# BUILD ONE RECORD  ->  exact output schema
# ============================================================


def build_record(
    row: pd.Series, verdict_text: str, year_int: int, category: str
) -> dict:
    """
    Converts a raw parquet row + judgment text into the target schema:
    {
        case_number,
        ipc_section   [ {section, section_number, offense_name, offense_category, is_primary} ],
        crime_keywords [ plain text keywords ],
        crime_details  (plain text),
        verdict        {outcome, disposal_nature, sentence, fine_inr, compensation_inr, detail}
    }
    """
    # Case number — prefer cnr, fall back to title, then synthesise
    cnr = str(row.get("cnr") or "").strip()
    title = str(row.get("title") or "").strip()
    case_number = (
        cnr
        if cnr and cnr.lower() != "nan"
        else (
            title if title and title.lower() != "nan" else f"SC Case / Year {year_int}"
        )
    )

    # Meta text for classification + crime description
    meta_text = " | ".join(
        [
            str(row.get("title", "") or ""),
            str(row.get("description", "") or ""),
            str(row.get("disposal_nature", "") or ""),
            str(row.get("citation", "") or ""),
        ]
    )

    combined = meta_text + "\n" + verdict_text

    if getattr(globals(), 'USE_LLM', False):
        llm_data = extract_with_llm(combined, category)
        ipc_sections = llm_data.get("ipc_section") or extract_ipc_sections(combined)
        crime_keywords = llm_data.get("crime_keywords") or extract_crime_keywords(combined)
        crime_details = llm_data.get("crime_details") or extract_crime_details(verdict_text, meta_text)
        verdict = llm_data.get("verdict") or extract_verdict(verdict_text, row.get("disposal_nature"))
        time.sleep(2)
    else:
        ipc_sections = extract_ipc_sections(combined)
        crime_keywords = extract_crime_keywords(combined)
        crime_details = extract_crime_details(verdict_text, meta_text)
        verdict = extract_verdict(verdict_text, row.get("disposal_nature"))

    return {
        "case_number": case_number,
        "ipc_section": ipc_sections,
        "crime_keywords": crime_keywords,
        "crime_details": crime_details,
        "verdict": verdict,
    }


# ============================================================
# MAIN
# ============================================================


def main():
    civil_cases: list = []
    criminal_cases: list = []
    traffic_cases: list = []

    started_at = datetime.now().isoformat()

    for year in range(END_YEAR, START_YEAR - 1, -1):
        if (
            len(civil_cases) >= MIN_EACH
            and len(criminal_cases) >= MIN_EACH
            and len(traffic_cases) >= MIN_EACH
        ):
            print("[INFO] All categories reached target. Stopping.")
            break

        df = fetch_parquet(year)
        if df is None or df.empty:
            continue

        print(f"[SCAN] {len(df)} rows for year {year} ...")

        for _, row in tqdm(df.iterrows(), total=len(df), desc=f"{year}"):
            if (
                len(civil_cases) >= MIN_EACH
                and len(criminal_cases) >= MIN_EACH
                and len(traffic_cases) >= MIN_EACH
            ):
                break

            # ── Text ────────────────────────────────────────────
            verdict_text = html_to_text(row.get("raw_html", ""))
            meta_text = " | ".join(
                [
                    str(row.get("title", "") or ""),
                    str(row.get("description", "") or ""),
                    str(row.get("disposal_nature", "") or ""),
                ]
            )
            combined = meta_text + "\n" + verdict_text

            # ── Year ────────────────────────────────────────────
            year_val = row.get("year")
            year_int = year
            try:
                if pd.notna(year_val):
                    year_int = int(year_val)
            except Exception:
                pass

            # ── Classify ────────────────────────────────────────
            is_traffic = contains_any(combined, TRAFFIC_KEYWORDS)
            is_criminal = contains_any(combined, CRIMINAL_KEYWORDS)
            is_civil = contains_any(combined, CIVIL_KEYWORDS)
            
            # Estimate a fallback category for LLM
            category_guess = "traffic" if is_traffic else ("criminal" if is_criminal else "civil")

            # ── Build record ────────────────────────────────────
            record = build_record(row, verdict_text, year_int, category_guess)

            # ── Bucket (overlap allowed) ─────────────────────────
            if is_traffic and len(traffic_cases) < MIN_EACH:
                traffic_cases.append({**record, "category": "traffic"})
            if is_criminal and len(criminal_cases) < MIN_EACH:
                criminal_cases.append({**record, "category": "criminal"})
            if (is_civil or (not is_traffic and not is_criminal)) and len(
                civil_cases
            ) < MIN_EACH:
                civil_cases.append({**record, "category": "civil"})

        print(
            f"[STATUS] civil={len(civil_cases)} | "
            f"criminal={len(criminal_cases)} | "
            f"traffic={len(traffic_cases)}"
        )
        time.sleep(1)

    # ============================================================
    # SAVE — single merged output file
    # ============================================================

    print("\n[INFO] Merging all categories and saving ...")

    def sanitize_record(r: dict) -> dict:
        return {
            k: sanitize(v) if not isinstance(v, (list, dict)) else v
            for k, v in r.items()
        }

    all_cases = (
        [sanitize_record(r) for r in civil_cases]
        + [sanitize_record(r) for r in criminal_cases]
        + [sanitize_record(r) for r in traffic_cases]
    )

    payload = {
        "_metadata": {
            "total_cases": len(all_cases),
            "civil_cases": len(civil_cases),
            "criminal_cases": len(criminal_cases),
            "traffic_cases": len(traffic_cases),
            "generated_at": datetime.now().isoformat(),
            "started_at": started_at,
            "source": "Indian Supreme Court Judgments — AWS Open Data (CC-BY 4.0)",
            "registry_url": "https://registry.opendata.aws/indian-supreme-court-judgments/",
            "s3_bucket": "s3://indian-supreme-court-judgments",
            "original_source": "https://scr.sci.gov.in",
            "coverage": f"{START_YEAR}–{END_YEAR}",
            "output_fields": {
                "case_number": "CNR / Case title from SC metadata",
                "ipc_section": "Extracted IPC sections — [{section, section_number, offense_name, offense_category, is_primary}]",
                "crime_keywords": "Keywords found in the case text matching the crime/category lists",
                "crime_details": "Plain-text crime summary extracted from judgment",
                "verdict": "{outcome, disposal_nature, sentence, fine_inr, compensation_inr, detail}",
                "category": "civil | criminal | traffic",
            },
        },
        "cases": all_cases,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[DONE] All cases saved -> {OUTPUT_FILE}  ({len(all_cases)} total cases)")
    print(
        f"       civil={len(civil_cases)} | criminal={len(criminal_cases)} | traffic={len(traffic_cases)}"
    )


if __name__ == "__main__":
    main()
