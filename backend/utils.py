import json
import os
import re

# Global cache for IPC data
IPC_DATA = []

def load_ipc_data():
    """
    Loads IPC JSON data into memory on startup.
    """
    global IPC_DATA
    try:
        json_path = os.path.join("laws_json", "ipc.json")
        if not os.path.exists(json_path):
            print(f"Warning: {json_path} not found.")
            return

        with open(json_path, "r", encoding="utf-8") as f:
            IPC_DATA = json.load(f)
        print(f"IPC Data loaded: {len(IPC_DATA)} sections.")
    except Exception as e:
        print(f"Error loading IPC data: {e}")

def get_relevant_sections(case_description, limit=15):
    """
    Scans the loaded IPC data and returns the most relevant sections 
    based on weighted keyword matching (Title > Description).
    """
    if not IPC_DATA:
        return ""

    try:
        # Pre-compile regex for efficiency
        tokenizer = re.compile(r'\w+')
        
        # 1. Normalize & Tokenize Case Description
        case_tokens = [word.lower() for word in tokenizer.findall(case_description)]
        case_keywords = set(case_tokens)
        
        # 2. Advanced Stop Words (Common English + Common Legal Terms)
        # Removed 'section' and numbers from stop words to ensure "Section 302" matches strongly
        stop_words = {
            'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'is', 'was', 'he', 'she', 'it', 'they', 
            'or', 'by', 'as', 'be', 'with', 'which', 'that', 'from', 'who', 'whom', 'whose', 'where', 'when',
            'shall', 'may', 'any', 'such', 'other', 'person', 'act', 'code', 'india', 'state', 'government',
            'public', 'offence', 'punishment', 'imprisonment', 'fine', 'description', 'term', 'years', 'two',
            'three', 'liable', 'committed', 'whoever', 'voluntarily', 'intentionally', 'causing', 'caused'
        }
        
        # Remove stopwords from query
        case_keywords = case_keywords - stop_words
        if not case_keywords:
            return "" # No useful keywords found

        scored_sections = []

        for item in IPC_DATA:
            if "Section" not in item or "section_title" not in item:
                continue
            
            section_score = 0
            
            # extract fields
            title_text = str(item.get("section_title", "")).lower()
            desc_text = str(item.get("section_desc", "")).lower()
            
            # Tokenize targets
            title_tokens = set(tokenizer.findall(title_text))
            desc_tokens = set(tokenizer.findall(desc_text))
            
            # --- SCORING LOGIC ---
            
            # 1. Title Matches (High Weight: 5 points per keyword)
            title_matches = case_keywords.intersection(title_tokens)
            section_score += len(title_matches) * 5
            
            # 2. Description Matches (Base Weight: 1 point per keyword)
            desc_matches = case_keywords.intersection(desc_tokens)
            section_score += len(desc_matches) * 1
            
            # 3. Exact Phrase Boost (Bonus: 10 points)
            # Check if any 2-word sequence from case exists in title (Basic phrase matching)
            for i in range(len(case_tokens) - 1):
                phrase = f"{case_tokens[i]} {case_tokens[i+1]}"
                if phrase in title_text:
                    section_score += 10
            
            # 4. Section Number Boost (Critical: 50 points)
            # If the LLM explicitly mentioned "Section 379", ensuring we prioritize Section 379
            # check if the item's section number is present in the search query tokens
            if str(item['Section']).lower() in case_keywords:
                 section_score += 50
            
            if section_score > 0:
                # Format: "Section X: Title - Desc"
                # Truncate description intelligently to save tokens but keep context
                full_desc = item.get('section_desc', '')
                truncated_desc = (full_desc[:400] + '...') if len(full_desc) > 400 else full_desc
                
                entry = f"IPC Section {item['Section']}: {item['section_title']}\n{truncated_desc}"
                scored_sections.append((section_score, entry))

        # Sort by score desc
        scored_sections.sort(key=lambda x: x[0], reverse=True)
        
        # Take top 'limit'
        top_sections = [entry for score, entry in scored_sections[:limit]]

        return "\n\n".join(top_sections)

    except Exception as e:
        print(f"Error finding relevant sections: {e}")
        return ""
