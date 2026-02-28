import json
import os
import re

# --- SEMANTIC ENHANCEMENT IMPORTS ---
try:
    import chromadb
    from chromadb.utils import embedding_functions
    HAS_SEMANTIC = True
except ImportError:
    HAS_SEMANTIC = False
    print("Warning: chromadb not installed. Semantic features disabled.")

CHROMA_CLIENT = None
CHROMA_COLLECTION = None
CASES_CHROMA_CLIENT = None
CASES_CHROMA_COLLECTION = None

def load_semantic_model():
    """Lazy load ChromaDB and its specific embedding function"""
    global CHROMA_CLIENT, CHROMA_COLLECTION
    if HAS_SEMANTIC and CHROMA_CLIENT is None:
        db_path = os.path.join(os.path.dirname(__file__), 'laws_chromadb')
        if os.path.exists(db_path):
            print("Connecting to ChromaDB for Legal Semantic Search...")
            CHROMA_CLIENT = chromadb.PersistentClient(path=db_path)
            
            # Using the same model we used to build the DB
            sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
            try:
                CHROMA_COLLECTION = CHROMA_CLIENT.get_collection(
                    name="indian_laws", 
                    embedding_function=sentence_transformer_ef
                )
            except ValueError:
                print("ChromaDB collection 'indian_laws' not found. Please run build_laws_chromadb.py first.")
        else:
            print(f"ChromaDB path '{db_path}' not found. Please run build_laws_chromadb.py first.")
            
    global CASES_CHROMA_CLIENT, CASES_CHROMA_COLLECTION
    if HAS_SEMANTIC and CASES_CHROMA_CLIENT is None:
        cases_db_path = os.path.join(os.path.dirname(__file__), 'cases_chromadb')
        if os.path.exists(cases_db_path):
            print("Connecting to ChromaDB for Cases Semantic Search...")
            CASES_CHROMA_CLIENT = chromadb.PersistentClient(path=cases_db_path)
            
            sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
            try:
                CASES_CHROMA_COLLECTION = CASES_CHROMA_CLIENT.get_collection(
                    name="historical_cases", 
                    embedding_function=sentence_transformer_ef
                )
            except ValueError:
                print("ChromaDB collection 'historical_cases' not found. Please run build_cases_chromadb.py first.")
        else:
            print(f"ChromaDB path '{cases_db_path}' not found. Please run build_cases_chromadb.py first.")

    return CHROMA_CLIENT, CHROMA_COLLECTION

def load_all_laws():
    """Stubbed out: We no longer need to manually loud laws into memory thanks to ChromaDB!"""
    pass

def get_relevant_sections(case_description, limit=15):
    try:
        # Extract potential section numbers from query (e.g., "Section 379")
        # This allows the explicit suggestions to override/boost semantic matches
        query_sections = set(re.findall(r"\b\d+[A-Za-z]?\b", case_description))

        # --- PURE SEMANTIC SEARCH USING CHROMADB ---
        if HAS_SEMANTIC:
            client, collection = load_semantic_model()
            if collection:
                # Query the Chroma Database (Returns L2 distances, lower is better)
                results = collection.query(
                    query_texts=[case_description],
                    n_results=limit * 2 # Fetch more to allow for section boosting re-ranking
                )
                
                if not results['ids'] or not results['ids'][0]:
                    return "No relevant laws found."

                scored_results = []
                for i in range(len(results['ids'][0])):
                    dist = results['distances'][0][i]  
                    meta = results['metadatas'][0][i]
                    
                    # Convert L2 distance into a 0-1 similarity score
                    base_score = 1.0 / (1.0 + dist)
                    score = base_score
                    
                    # Generalized Boost: If section number is in query, Boost it!
                    if str(meta.get('section', '')) in query_sections:
                        score += 0.5  # Huge boost
                        reasoning = f"Semantic Match + Explicit Query Boost ({meta.get('section')})"
                    else:
                        reasoning = f"Semantic Match: {base_score:.2f}"
                        
                    scored_results.append({
                        "meta": meta,
                        "score": score,
                        "details": reasoning
                    })
                    
                # Re-sort after boosting by our custom score
                scored_results.sort(key=lambda x: x["score"], reverse=True)
                
                formatted_outputs = []
                for entry in scored_results[:limit]:
                    meta = entry["meta"]
                    desc = meta.get("desc", "")
                    trunc_desc = (desc[:400] + "...") if len(desc) > 400 else desc
                    
                    out_str = f"[{meta.get('law')}] Section {meta.get('section')}: {meta.get('title')}\n{trunc_desc}\n[Reasoning: {entry['details']} (Score: {entry['score']:.2f})]"
                    formatted_outputs.append(out_str)
                    
                return "\n\n".join(formatted_outputs)

        return "Semantic search is disabled. Please `pip install chromadb` and build the DB."

    except Exception as e:
        print(f"Error querying ChromaDB: {e}")
        return ""

def get_relevant_cases(case_description, limit=3):
    try:
        if HAS_SEMANTIC:
            load_semantic_model() # Make sure case db is loaded
            if CASES_CHROMA_COLLECTION:
                results = CASES_CHROMA_COLLECTION.query(
                    query_texts=[case_description],
                    n_results=limit
                )
                
                if not results['ids'] or not results['ids'][0]:
                    return "No relevant historical cases found."

                formatted_outputs = []
                for i in range(len(results['ids'][0])):
                    doc = results['documents'][0][i]
                    meta = results['metadatas'][0][i]
                    dist = results['distances'][0][i]
                    
                    # Convert L2 distance into a 0-1 similarity score
                    score = 1.0 / (1.0 + dist)
                    
                    out_str = (
                        f"--- Historical Case Match (Similarity: {score:.2f}) ---\n"
                        f"Facts: {doc}\n"
                        f"Sections Applied: {meta.get('sections_applied')}\n"
                        f"Outcome: {meta.get('outcome')} | Jail Term: {meta.get('jail_term')} | Fine: ₹{meta.get('fine_inr')}\n"
                        f"Verdict Details: {meta.get('detail')}"
                    )
                    formatted_outputs.append(out_str)
                    
                return "\n\n".join(formatted_outputs)

        return "Semantic search is disabled for cases. Please `pip install chromadb` and build the historical cases DB."

    except Exception as e:
        print(f"Error querying Cases ChromaDB: {e}")
        return ""
