import os
import json
import chromadb
from chromadb.utils import embedding_functions

def load_laws_data(laws_dir):
    documents = []
    metadatas = []
    ids = []
    
    print(f"Loading JSON files from {laws_dir}...")
    idx = 0
    for file_name in os.listdir(laws_dir):
        if file_name.endswith('.json'):
            file_path = os.path.join(laws_dir, file_name)
            law_name = file_name.replace('.json', '').upper()
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    sections = json.load(f)
                    for item in sections:
                        # Handle potential missing keys gracefully depending on schema variations
                        section_num = item.get("Section", item.get("section", ""))
                        sec_title = item.get("section_title", "")
                        sec_desc = item.get("section_desc", "")
                        
                        # Only add if we have some text
                        if str(section_num) or sec_title or sec_desc:
                            # Create a cohesive chunk for the embedding
                            text_chunk = f"{law_name} Section {section_num}: {sec_title}. {sec_desc}".strip()
                            
                            metadata = {
                                "law": law_name,
                                "chapter": item.get("chapter", ""),
                                "section": str(section_num),
                                "title": sec_title,
                                "desc": sec_desc
                            }
                            
                            # ChromaDB requires IDs to be strings
                            doc_id = f"{law_name}_{section_num}_{idx}"
                            
                            documents.append(text_chunk)
                            metadatas.append(metadata)
                            ids.append(doc_id)
                            idx += 1
            except Exception as e:
                print(f"Error loading {file_name}: {e}")
                
    return documents, metadatas, ids

def build_vector_db():
    laws_dir = os.path.join(os.path.dirname(__file__), 'laws_json')
    db_path = os.path.join(os.path.dirname(__file__), 'laws_chromadb')
    
    documents, metadatas, ids = load_laws_data(laws_dir)
    
    if not documents:
        print("No data found to process.")
        return

    print("Initializing ChromaDB persistent client...")
    client = chromadb.PersistentClient(path=db_path)
    
    # We use the default all-MiniLM-L6-v2 model 
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    # Re-create the collection to ensure it's fresh
    try:
        client.delete_collection(name="indian_laws")
    except Exception:
        pass # Collection didn't exist yet
        
    print("Creating collection 'indian_laws'...")
    collection = client.create_collection(
        name="indian_laws",
        embedding_function=sentence_transformer_ef
    )
    
    # Add items to Chroma DB in batches to prevent memory overflow
    BATCH_SIZE = 5000
    print(f"Adding {len(documents)} sections to Vector Database in batches of {BATCH_SIZE}...")
    
    for i in range(0, len(documents), BATCH_SIZE):
        end_idx = min(i + BATCH_SIZE, len(documents))
        print(f"  -> Processing batch {i} to {end_idx}...")
        collection.add(
            documents=documents[i:end_idx],
            metadatas=metadatas[i:end_idx],
            ids=ids[i:end_idx]
        )
        
    print(f"✅ Vector DB setup successfully! Stored at '{db_path}'")
    print(f"Collection currently contains {collection.count()} documents.")

if __name__ == "__main__":
    build_vector_db()
