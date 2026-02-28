from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import json
from groq import Groq
from models import (
    FIRRequest,
    QuestionnaireRequest,
    ChargeSheetRequest,
    VerdictRequest,
    FairnessRequest,
)

load_dotenv()

app = FastAPI(title="FIR Generator API")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all. Restrict in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Groq Client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("Warning: GROQ_API_KEY not found in environment variables.")

client = Groq(api_key=GROQ_API_KEY)

from utils import load_semantic_model, get_relevant_sections, get_relevant_cases

# Load ChromaDB connections into memory on startup
load_semantic_model()


@app.post("/api/generate_fir")
async def generate_fir(request: FIRRequest):
    try:
        # Retrieve Relevant Laws based on case description
        relevant_laws = get_relevant_sections(request.case_description, limit=5)
        print(f"Context injected: {len(relevant_laws)} chars")

        # Construct the prompt based on user requirements
        complainant_info = f"Name: {request.complainant.name}, Address: {request.complainant.address}, Contact: {request.complainant.contact}"
        accused_info = f"Name: {request.accused.name if request.accused else 'Unknown person(s)'}, Address: {request.accused.address if request.accused else 'Not provided'}"

        # New Official Info
        official_info = f"""
        Police Station: {request.police_station}
        FIR Number: {request.fir_number}
        Registration Date: {request.registration_date}
        Investigating Officer: {request.officer_name} ({request.officer_rank})
        """

        # --- STEP 0: PRE-CHECK VALIDATION ---
        check_prompt = f"""
        Evaluate this case description text. Is it a meaningful (even if brief) description of a criminal incident, dispute, or legal case?
        Or is it gibberish, meaninglessly short, or entirely irrelevant?
        
        Text: "{request.case_description}"
        
        Respond with ONLY 'VALID' if it is meaningful enough to process, or 'INVALID' if it is gibberish/not a case. No other words.
        """

        check_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": check_prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.0,
            max_tokens=10,
        )
        if "INVALID" in check_completion.choices[0].message.content.upper():
            raise HTTPException(
                status_code=400,
                detail="The case description provided is too vague, short, or meaningless. Please provide a clear, detailed description of the incident.",
            )

        # --- STEP 1: SEMANTIC QUERY EXPANSION ---
        # Ask LLM to identify potential IPC sections and legal terms from the informal description
        # This acts as a bridge between "User Language" and "Legal Language"
        expansion_prompt = f"""
        Analyze this criminal case description and list the top 5 most relevant Indian Law Section Numbers (e.g. IPC, CrPC, MVA, NIA, etc.) and Legal Keywords.
        Return ONLY a comma-separated list.
        
        Case: "{request.case_description}"
        
        Example Output: Section 378, Theft, Section 379, Movable Property, Dishonest Intention
        """

        expansion_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": expansion_prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=50,
        )
        legal_keywords = expansion_completion.choices[0].message.content
        print(f"Semantic Expansion: {legal_keywords}")

        # --- STEP 2: RETRIEVAL ---
        # Combine user description with expert keywords for a rich search query
        search_query = f"{request.case_description} {legal_keywords}"
        relevant_laws_raw = get_relevant_sections(search_query, limit=5)
        print(f"Initial Context injected: {len(relevant_laws_raw)} chars")
        print(
            f"\n--- [RAG] INITIAL FETCHED LAWS ---\n{relevant_laws_raw}\n----------------------------------"
        )

        # --- STEP 3: VERIFICATION / RELEVANCE FILTERING ---
        verification_prompt = f"""
        You are a strict Legal Assessor and Expert.
        Below is a case description and a set of potentially relevant Indian Law sections (fetched via vector search).
        Carefully evaluate each section and determine if it is ACTUALLY relevant to the specific facts of the case.
        
        Case Description: "{request.case_description}"
        
        Fetched Sections:
        {relevant_laws_raw}
        
        Task:
        1. Select and return ONLY the TOP most relevant Indian Penal Code (IPC) and other law sections that are genuinely applicable to the case. Keep the original text structure of the relevant sections.
        2. If a section from the 'Fetched Sections' is irrelevant or weakly related, DROP IT entirely.
        3. CRITICAL: If the fetched sections do not contain the top most relevant IPC sections for this specific crime, or if they are entirely irrelevant, YOU MUST use your own legal knowledge to modify the list. You must add the correct and top relevant IPC, CrPC, or other relevant law sections along with a brief description of each section.
        Do not add any conversational filler. Treat your response as the final filtered context.
        """

        verification_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": verification_prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=1500,
        )

        relevant_laws = verification_completion.choices[0].message.content
        print(f"Verified Context injected: {len(relevant_laws)} chars")
        print(
            f"\n--- [RAG] VERIFIED LAWS FILTERED ---\n{relevant_laws}\n------------------------------------"
        )

        system_prompt = f"""You are an expert Indian Police Officer and Legal Drafting Assistant with deep knowledge of the Indian Penal Code (IPC), CrPC, Motor Vehicles Act (MVA), and other standard Indian Laws.

Your task is to convert informal user-provided case details into a legally structured First Information Report (FIR).

Here is the Reference Law Data for your knowledge. Use this to explicitly cite the correct sections:
<LEGAL_CONTEXT>
{relevant_laws}
</LEGAL_CONTEXT>

STRICTLY FOLLOW THE FIR FORMAT BELOW:

-------------------------------
FIRST INFORMATION REPORT (FIR)
-------------------------------

1. Police Station: <Police Station>
2. FIR Number: <FIR Number>
3. Date and Time of Registration: <Registration Date>

4. Complainant (Plaintiff) Details:
   Name: <Name>
   Address: <Address>
   Contact Details: <Contact>
   (If any field is missing, clearly write "Not provided")

5. Accused (Defendant) Details:
   (Mention name and address if provided, otherwise write "Unknown person(s)")

6. Date, Time, and Place of Occurrence:
   (Mention only if clearly stated in the case description, otherwise write "Not provided")

7. Sections of Law Applied:
   - [ACT Name] Section <number> – <title>
   - [ACT Name] Section <number> – <title>
   - [ACT Name] Section <number> – <title>
   (Briefly explain why these sections apply based on the facts. YOU MUST INCLUDE AT LEAST 3 DISTINCT RELEVANT SECTIONS. If the case is simple, consider related offenses like attempt, abetment, or common intention to reach 3 sections.)

8. Facts of the Case:
   (Formally narrate the incident in third-person legal language using phrases like
   “It is alleged that…”, strictly based on the case description.)

9. Investigating Officer:
   Name: <Investigating Officer Name>
   Rank: <Rank>

10. Signature / Thumb Impression of Complainant: Not provided

MANDATORY DISCLAIMER (MUST BE INCLUDED AT THE END):
“This FIR has been generated by an AI system for academic and assistive purposes only and does not have legal validity unless reviewed and registered by authorized police officials.”

MANDATORY DISCLAIMER (MUST BE INCLUDED AT THE END):
“This FIR has been generated by an AI system for academic and assistive purposes only and does not have legal validity unless reviewed and registered by authorized police officials.”

IMPORTANT: Generate the output strictly in English.
"""

        user_content = f"""
Input Details:
1. CONSTANT DETAILS (Use these exactly):
{official_info}

2. Complainant Details: {complainant_info}
3. Accused Details: {accused_info}
4. Case Description: {request.case_description}
5. Date/Time/Place Note: {request.date_time_place}
"""

        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
        )

        generated_fir = completion.choices[0].message.content
        return {"fir": generated_fir}

    except Exception as e:
        print(f"Error generating FIR: {str(e)}")  # Log the error
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate_questionnaire")
async def generate_questionnaire(request: QuestionnaireRequest):
    try:
        system_prompt = """You are an experienced Investigating Officer. 
        Your task is to review an FIR and generate a set of cross-examination questions to investigate the case further.
        
        Generate exactly 5 critical questions for the Complainant (Plaintiff) and 5 critical questions for the Accused (Defendant).
        ALSO, generate "simulated" answers for these questions based on the likely facts of the case.
        - Plaintiff answers should support the FIR.
        - Defendant answers should deny/defend/explain.
        
        Output format must be valid JSON:
        {
            "plaintiff_questions": ["Q1", "Q2", "Q3", "Q4", "Q5"],
            "plaintiff_simulated_answers": ["A1", "A2", "A3", "A4", "A5"],
            "defendant_questions": ["Q1", "Q2", "Q3", "Q4", "Q5"],
            "defendant_simulated_answers": ["A1", "A2", "A3", "A4", "A5"]
        }
        
        IMPORTANT: Generate the output strictly in English.
        """

        user_content = f"""
        Case Description: {request.case_description}
        FIR Content:
        {request.fir_content}
        """

        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.4,
            response_format={"type": "json_object"},
        )

        return json.loads(completion.choices[0].message.content)

    except Exception as e:
        print(f"Error generating questionnaire: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate_charge_sheet")
async def generate_charge_sheet(request: ChargeSheetRequest):
    try:
        system_prompt = """You are a Senior Police Officer responsible for filing the Final Report (Charge Sheet) under Section 173 CrPC.
        
        Based on the FIR and the interrogation answers (investigation findings), draft a formal Charge Sheet.
        
        STRICT FORMATTING RULES:
        1.  **Main Header**: "IN THE COURT OF CHIEF JUDICIAL MAGISTRATE, VIZIANAGARAM" (H1 Header, Uppercase).
        2.  **No AI Disclaimers**: Absolutely none.
        3.  **Layout**:
            -   Use H2 for Section Titles (e.g., "1. POLICE REPORT NO.", "2. ACCUSED DETAILS").
            -   Use standard paragraphs for content.
            -   Ensure there is ample spacing (use line breaks) between sections.
        
        **CONTENT SECTIONS**:
        
        # IN THE COURT OF CHIEF JUDICIAL MAGISTRATE, VIZIANAGARAM

        ## 1. POLICE REPORT & DETAILS
        **FIR No:** ... | **Date:** ... | **Police Station:** ...

        ## 2. DETAILS OF ACCUSED PERSON(S)
        Name: ...
        Address: ...

        ## 3. NATURE OF OFFENCE (SECTIONS OF LAW)
        ...

        ## 4. BRIEF FACTS OF THE CASE
        ...

        ## 5. INVESTIGATION FINDINGS & QUESTIONNAIRE
        (Write a brief summary and then YOU MUST INCLUDE the exact cross-examination Questions and Answers for both the Complainant and the Accused here).
        ...

        ## 6. CHARGES FRAMED
        The investigation has established prima facie evidence against the accused for offenses under:
        ...

        ## 7. LIST OF WITNESSES
        1. Complainant: ...
        2. Investigating Officer: {request.officer_name}, {request.officer_rank}

        ## 8. PRAYER TO THE COURT
        ## 8. PRAYER TO THE COURT
        It is respectfully prayed that the Honorable Court may take cognizance of the offenses...
        
        IMPORTANT: Generate the output strictly in English.
        """

        # Format Q&A for the model
        p_qa = "\n".join(
            [f"Q: {q}\nA: {a}" for q, a in request.plaintiff_answers.items()]
        )
        d_qa = "\n".join(
            [f"Q: {q}\nA: {a}" for q, a in request.defendant_answers.items()]
        )

        user_content = f"""
        FIR Context:
        {request.fir_content}
        
        Investigation Findings:
        --- Plaintiff (Complainant) Interrogation ---
        {p_qa}
        
        --- Defendant (Accused) Interrogation ---
        {d_qa}

        --- Investigation Synopsis ---
        {request.investigation_summary}
        
        Officer Submitting: {request.officer_name}, {request.officer_rank}
        Police Station: {request.police_station}
        """

        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
        )

        return {"charge_sheet": completion.choices[0].message.content}

    except Exception as e:
        print(f"Error generating charge sheet: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/predict_verdict")
async def predict_verdict(request: VerdictRequest):
    try:
        # 1. Fetch historical cases related to this case
        historical_cases_raw = get_relevant_cases(request.case_description, limit=5)
        print(f"\n[RAG] Initial Historical Cases fetched.")

        # 2. Add an agentic verification step to ensure they are genuinely relevant
        verification_prompt = f"""
        You are a highly analytical Legal Assessor.
        You have been given a case description and some potentially relevant historical case precedents retrieved by a vector database search.
        Carefully evaluate the historical cases. If they are irrelevant, drop them. Return only the relevant cases and provide a 1-sentence reasoning for why they establish precedent for the case at hand.
        
        Current Case Description: "{request.case_description}"
        
        Retrieved Historical Precedents:
        {historical_cases_raw}
        
        Task:
        Filter the historical precedents. Return ONLY the relevant historical cases along with a brief reason for their relevance. If none are relevant, return "No strictly relevant precedents established."
        """

        verification_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": verification_prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=1500,
        )

        historical_cases_context = verification_completion.choices[0].message.content
        print(
            f"[RAG] Verified Historical Cases injected: {len(historical_cases_context)} characters"
        )
        print(
            f"\n--- [RAG] FILTERED VERIFIED PRECEDENTS ---\n{historical_cases_context}\n--------------------------------------"
        )

        system_prompt = f"""You are a highly experienced Indian Judge.
        
        Your task is to review the Charge Sheet and Case Description and predict the most likely legal verdict based on the Indian Penal Code (IPC) and CrPC.
        
        To guide your judgment and to remain consistent with established precedent, here are some historical case rulings similar to this one:
        <HISTORICAL_PRECEDENTS>
        {historical_cases_context}
        </HISTORICAL_PRECEDENTS>
        
        Specifically, you must determine:
        1. Whether the accused is likely to be convicted (Guilty) or acquitted (Not Guilty).
        2. If Guilty, predict the likely Punishment:
           - Jail Term (Years/Months)
           - Fine Amount (in INR)
           - Rationale (Brief legal reasoning comparing facts to precedents if applicable)
        
        Output format must be valid JSON:
        {{
            "verdict": "Guilty" or "Not Guilty" or "Partially Guilty",
            "punishment_type": "Jail" or "Fine" or "Both" or "None",
            "jail_term": "e.g. 3 years Rigorous Imprisonment" (or "None"),
            "fine_amount": "e.g. ₹10,000" (or "None"),
            "legal_rationale": "Brief explanation of why this verdict is appropriate based on the sections cited and facts."
        }}
        
        IMPORTANT: Generate the output strictly in English.
        """

        user_content = f"""
        Case Description: {request.case_description}
        Charge Sheet Content:
        {request.charge_sheet_content}
        """

        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        return json.loads(completion.choices[0].message.content)

    except Exception as e:
        print(f"Error predicting verdict: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def read_root():
    return {"message": "FIR Generator API is running"}


@app.post("/api/analyze_fairness")
async def analyze_fairness(request: FairnessRequest):
    try:
        system_prompt = """You are a highly objective Judicial Auditor focused on ensuring fair, unbiased legal outcomes.
        
        Your task is to analyze the provided Case Description, Charge Sheet, and the initial Predicted Verdict.
        Determine if the proceedings and the predicted verdict are completely fair and logically sound.
        
        CRITICAL RULE FOR EFFICIENCY: You should default to labeling the verdict as "Fair" in most cases. Minor discrepancies, small formatting issues, or slight logical assumptions should be noted in your explanation but MUST NOT cause the label to be "Needs Review".
        ONLY use "Unfair" or "Needs Review" if there is blatant demographic bias, glaring logical hallucinations, extreme severity mismatches, or undeniable evidence that the verdict directly contradicts the facts.
        
        Output format must be valid JSON:
        {
            "overall_label": "Fair" or "Unfair" or "Needs Review",
            "explanation": "Provide a quick, concise explanation on why you chose this label based on the evidence."
        }
        
        IMPORTANT: Generate the output strictly in English.
        """

        user_content = f"""
        Case Description: {request.case_description}
        Original Verdict: {request.original_verdict}
        Charge Sheet Content (Includes Interrogation):
        {request.charge_sheet_content}
        """

        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        return json.loads(completion.choices[0].message.content)

    except Exception as e:
        print(f"Error in fairness analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
