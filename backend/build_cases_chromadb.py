import os
import json
import chromadb
from chromadb.utils import embedding_functions

def load_cases_data(dataset_path):
    documents = []
    metadatas = []
    ids = []
    
    print(f"Loading cases from {dataset_path}...")
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            cases = data.get("cases", [])
            
            for idx, case in enumerate(cases):
                case_number = case.get("case_number", f"Case_Unknown_{idx}")
                crime_details = case.get("crime_details", "")
                
                # We need details to make a meaningful embedding
                if not crime_details:
                    continue
                
                # Compress verdict for metadata reference
                verdict = case.get("verdict", {})
                outcome = verdict.get("outcome", "Unknown")
                jail_term = verdict.get("sentence", "None")
                fine_inr = verdict.get("fine_inr", 0)
                
                # Create a concise textual representation for embedding
                # So we can match user cases by their case description
                text_chunk = f"Case Facts: {crime_details}"
                
                # IPC Sections
                ipc_list = [sec.get("section") for sec in case.get("ipc_section", []) if sec.get("section")]
                sections_str = ", ".join(ipc_list) if ipc_list else "None specified"
                
                metadata = {
                    "case_number": case_number,
                    "sections_applied": sections_str,
                    "outcome": str(outcome),
                    "jail_term": str(jail_term),
                    "fine_inr": str(fine_inr),
                    "detail": str(verdict.get("detail", ""))
                }
                
                doc_id = f"case_{idx}"
                documents.append(text_chunk)
                metadatas.append(metadata)
                ids.append(doc_id)
                
    except Exception as e:
        print(f"Error loading cases dataset: {e}")
                
    return documents, metadatas, ids

def build_cases_vector_db():
    dataset_path = os.path.join(os.path.dirname(__file__), 'cases_ipc_crime_verdict.json')
    db_path = os.path.join(os.path.dirname(__file__), 'cases_chromadb')
    
    documents, metadatas, ids = load_cases_data(dataset_path)
    
    if not documents:
        print("No data found to process.")
        return

    print("Initializing ChromaDB persistent client...")
    client = chromadb.PersistentClient(path=db_path)
    
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    try:
        client.delete_collection(name="historical_cases")
    except Exception:
        pass 
        
    print("Creating collection 'historical_cases'...")
    collection = client.create_collection(
        name="historical_cases",
        embedding_function=sentence_transformer_ef
    )
    
    BATCH_SIZE = 5000
    print(f"Adding {len(documents)} cases to Vector Database in batches of {BATCH_SIZE}...")
    
    for i in range(0, len(documents), BATCH_SIZE):
        end_idx = min(i + BATCH_SIZE, len(documents))
        print(f"  -> Processing batch {i} to {end_idx}...")
        collection.add(
            documents=documents[i:end_idx],
            metadatas=metadatas[i:end_idx],
            ids=ids[i:end_idx]
        )
        
    print(f"✅ Historical Cases Vector DB setup successfully! Stored at '{db_path}'")
    print(f"Collection currently contains {collection.count()} documents.")

if __name__ == "__main__":
    build_cases_vector_db()
