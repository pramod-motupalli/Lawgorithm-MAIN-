import json
import os
import re

# Global cache for Law data
LAWS_DATA = []

def load_all_laws():
    """
    Loads all JSON law data from the 'laws_json' directory into memory on startup.
    Normalizes schema to have 'act', 'section', 'title', 'description'.
    """
    global LAWS_DATA
    LAWS_DATA = [] # Reset
    
    laws_dir = os.path.join(os.path.dirname(__file__), "laws_json")
    if not os.path.exists(laws_dir):
        print(f"Warning: Directory {laws_dir} not found.")
        return

    try:
        # Iterate over all json files
        for filename in os.listdir(laws_dir):
            if not filename.lower().endswith(".json"):
                continue
                
            filepath = os.path.join(laws_dir, filename)
            act_name = os.path.splitext(filename)[0].upper() # e.g., 'ipc.json' -> 'IPC'
            
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # Normalize and add to global list
                    count = 0
                    for item in data:
                        # Handle varied schema keys
                        # Section number
                        section = item.get("Section") or item.get("section")
                        if not section: continue
                        
                        # Title
                        title = item.get("section_title") or item.get("title") or ""
                        
                        # Description
                        desc = item.get("section_desc") or item.get("description") or ""
                        
                        normalized_entry = {
                            "act": act_name,
                            "section": str(section),
                            "title": title,
                            "description": desc
                        }
                        LAWS_DATA.append(normalized_entry)
                        count += 1
                        
                    print(f"Loaded {count} sections from {act_name}")
                    
            except Exception as e:
                print(f"Error loading {filename}: {e}")
                
        print(f"Total Laws Loaded: {len(LAWS_DATA)} sections across all acts.")

    except Exception as e:
        print(f"Error scanning laws directory: {e}")

def get_relevant_sections(case_description, limit=15):
    """
    Scans ALL loaded Law data and returns the most relevant sections 
    based on weighted keyword matching (Title > Description).
    """
    if not LAWS_DATA:
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

        for item in LAWS_DATA:
            section_score = 0
            
            # extract fields
            title_text = str(item.get("title", "")).lower()
            desc_text = str(item.get("description", "")).lower()
            act_text = str(item.get("act", "")).lower()
            
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
            for i in range(len(case_tokens) - 1):
                phrase = f"{case_tokens[i]} {case_tokens[i+1]}"
                if phrase in title_text:
                    section_score += 10
            
            # 4. Section Number Boost (Critical: 50 points)
            if str(item['section']).lower() in case_keywords:
                 section_score += 50
            
            # 5. Act Name Match (Moderate: 20 points) - e.g. if user says "MVA" or "Motor Vehicle"
            if act_text in case_tokens: # simple match 'ipc' in ['ipc', '302']
                section_score += 20
            
            if section_score > 0:
                # Format: "[ACT] Section X: Title - Desc"
                full_desc = item.get('description', '')
                truncated_desc = (full_desc[:400] + '...') if len(full_desc) > 400 else full_desc
                
                entry = f"[{item['act']}] Section {item['section']}: {item['title']}\n{truncated_desc}"
                scored_sections.append((section_score, entry))

        # Sort by score desc
        scored_sections.sort(key=lambda x: x[0], reverse=True)
        
        # Take top 'limit'
        top_sections = [entry for score, entry in scored_sections[:limit]]

        return "\n\n".join(top_sections)

    except Exception as e:
        print(f"Error finding relevant sections: {e}")
        return ""
