from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import json
from groq import Groq
from models import *

load_dotenv()

app = FastAPI(title="Lawgorithm API")

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

        # --- STEP 1: AGENT GUESSES POSSIBLE SECTIONS ---
        guess_prompt = f"""
        Based on the following case description, act as a legal expert and guess the possible legal sections from the Indian Penal Code (IPC),CPC,HMA,IDA,IEA,MVA,NIA and Code of Criminal Procedure (CrPC).
        List the section numbers and a brief keyword for each. This will be used to fetch vectors from a database.
        
        Case Description: "{request.case_description}"
        
        Respond ONLY with a comma-separated list of guessed sections and keywords (e.g. IPC Section 378 - Theft, IPC Section 379, CrPC Section 154).
        """

        guess_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": guess_prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=100,
        )
        guessed_sections = guess_completion.choices[0].message.content
        print(f"Guessed Sections: {guessed_sections}")

        # --- STEP 2: FETCH VECTORS BASED ON USER INPUTS & GUESSED SECTIONS ---
        search_query = f"{request.case_description} {guessed_sections}"
        fetched_relevant_sections_raw = get_relevant_sections(search_query, limit=10)
        print(
            f"Fetched Sections context size: {len(fetched_relevant_sections_raw)} chars"
        )

        # --- STEP 3: VERIFICATION AND MODIFICATION ---
        verification_prompt = f"""
        You are an expert Indian Legal Assessor and Judicial Officer.
        You have been given a user case description, guessed sections from an AI assistant, and fetched legal section texts from a database.
        
        Your task is to verify if the fetched sections and guessed sections are TRULY related to the case.
        - If the fetched sections are related, select the most relevant ones.
        - If they are NOT related, or crucial sections are missing, you MUST modify the results and include the correct sections from your own knowledge of IPC and CrPC.
        
        Case Description: "{request.case_description}"
        
        Guessed Sections from AI assistant: 
        {guessed_sections}
        
        Fetched Sections from DB:
        {fetched_relevant_sections_raw}
        
        Output ONLY the final list of the 3-5 most specific, confirmed relevant sections. 
        Format cleanly with the section title and a 1-sentence explanation of why it precisely applies to the facts of the case. No conversational filler.
        """

        verification_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": verification_prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=1500,
        )

        relevant_laws = verification_completion.choices[0].message.content
        print(f"Verified Context injected: {len(relevant_laws)} chars")
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
        # --- END-TO-END HISTORICAL CASE RETRIEVAL AGENT ---
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_historical_cases",
                    "description": "Searches the historical case vector database for cases matching the query.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query. For better results, describe the crime type, specific facts, and relevant legal keywords (e.g. 'theft, stolen mobile phone, section 378').",
                            },
                        },
                        "required": ["query"],
                    },
                },
            }
        ]

        system_msg = """You are an end-to-end autonomous Precedent Retrieval Agent. 
Your goal is to find 3-5 HIGHLY RELEVANT historical case precedents that establish standard rulings for a given case description and Charge Sheet.

STEPS YOU MUST FOLLOW:
1. Carefully analyze the facts of the case description AND the sections of law applied in the Charge Sheet.
2. Call the `search_historical_cases` tool with a highly specific query containing the exact Section Numbers applied and key facts (e.g., 'Section 392 IPC robbery gold chain').
3. Read the fetched historical cases. Verify if they match the core facts and nature of the current case, particularly matching the sections of law.
4. CRITICAL: If they do NOT match (e.g. you searched for theft but got a bus accident or dowry case), YOU MUST reject them.
5. If your initial queries fail to bring back relevant cases, formulate BROADER queries. Search for the root legal terms rather than ultra-specific facts (e.g. use "robbery Section 392" or "theft Section 378" instead of "snatching gold chain from a person on a bike").
6. Once you have fetched truly relevant historical cases, output the final list of the relevant cases and provide a 1-sentence reasoning for why they establish precedent for the case at hand.
If none are relevant after 4 tries, return "No strictly relevant precedents established."
Do not include conversational filler in your final output.
"""
        messages = [
            {"role": "system", "content": system_msg},
            {
                "role": "user",
                "content": f"Case Description: {request.case_description}\n\nCharge Sheet Content (Read for Sections): {request.charge_sheet_content}",
            },
        ]

        historical_cases_context = ""
        max_iterations = 4
        for i in range(max_iterations):
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.1,
                max_tokens=2000,
            )

            response_message = response.choices[0].message

            message_dict = {"role": "assistant"}
            if response_message.content:
                message_dict["content"] = response_message.content
            if response_message.tool_calls:
                message_dict["tool_calls"] = [
                    {
                        "id": tool.id,
                        "type": "function",
                        "function": {
                            "name": tool.function.name,
                            "arguments": tool.function.arguments,
                        },
                    }
                    for tool in response_message.tool_calls
                ]
            messages.append(message_dict)

            # Execute tool calls if any
            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    if tool_call.function.name == "search_historical_cases":
                        try:
                            args = json.loads(tool_call.function.arguments)
                            query = args.get("query", request.case_description)
                        except:
                            query = request.case_description

                        print(f"Agent searching Cases DB with query: {query}")
                        search_results = get_relevant_cases(query, limit=5)

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_call.function.name,
                                "content": search_results
                                or "No results found. Try a different query.",
                            }
                        )
            else:
                historical_cases_context = response_message.content
                break
        else:
            if messages[-1].get("content"):
                historical_cases_context = messages[-1]["content"]
            else:
                historical_cases_context = (
                    "No strictly relevant precedents established."
                )

        print(f"Historical Cases Agent Output Length: {len(historical_cases_context)}")

        system_prompt = f"""You are a highly experienced Indian Judge.
        
        Your task is to review the Charge Sheet and Case Description and predict the most likely legal verdict based on the Indian Penal Code (IPC) and CrPC.
        
        To guide your judgment and to remain strictly consistent with established precedent, here are some historical case rulings similar to this one:
        <HISTORICAL_PRECEDENTS>
        {historical_cases_context}
        </HISTORICAL_PRECEDENTS>
        
        Specifically, you must determine:
        1. Whether the accused is likely to be convicted (Guilty) or acquitted (Not Guilty).
        2. If Guilty, predict the likely Punishment:
           - Jail Term (Years/Months)
           - Fine Amount (in INR)
           - Rationale (Brief legal reasoning comparing facts to precedents if applicable)
        
        CRITICAL INSTRUCTION FOR CONSISTENCY: If the case at hand has the exact same severity and matching facts/sections as one of the Historical Precedents, YOU MUST give the exact same Jail Term and Fine as that historical case. Do not deviate from the precedent's punishment unless there are clear aggravating or mitigating circumstances.
        
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
    return {"message": "Lawgorithm API is running"}


@app.post("/api/analyze_fairness")
async def analyze_fairness(request: FairnessRequest):
    try:
        system_prompt = """You are a highly objective Judicial Auditor focused on ensuring fair, unbiased legal outcomes.

Your task is to evaluate the provided Case Description, Charge Sheet, and Predicted Verdict to determine if the proceedings align with standard legal and ethical practices.

Guiding Principles for Evaluation:
The legal system relies on reasonable alignment between facts and charges. Approach every case with a baseline presumption of procedural fairness. A case should be deemed "Fair" as long as the verdict is logically connected to the charges applied, acknowledging that stylistic differences in drafting or minor informational gaps are normal in legal documentation and do not constitute prejudice.

You should reserve the "Needs Review" or "Unfair" classifications exclusively for instances where the documentation demonstrates:
- Clearly stated demographic prejudice (e.g., bias related to caste, religion, gender, or race).
- A severe disproportion between the offense and the penalty (e.g., recommending maximum statutory punishments for trivial infractions).
- Fundamental contradictions where the accused is penalized despite facts explicitly precluding their involvement.

In all other scenarios, including instances where you might simply recommend minor improvements or note formatting issues, the case should be validated as "Fair".

Output format must be valid JSON:
{
    "overall_label": "Fair" or "Unfair" or "Needs Review",
    "explanation": "Provide a concise, professional explanation supporting the selected label, referencing material evidence only."
}

Please ensure your analysis is generated strictly in English.
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
