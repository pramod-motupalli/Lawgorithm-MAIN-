# Police DraftAssist - Backend API

## Overview
This is the backend service for the **Police DraftAssist** application. It provides a RESTful API to generate legally structured First Information Reports (FIRs) using AI.

It is built with **FastAPI** and integrates with **Groq (Llama 3.3 70B)** for text generation.

## Key Features
- **AI-Powered FIR Drafting**: Converts informal case descriptions into official FIR format.
- **Smart Legal Context**:
    - Uses a **Semantic Query Expansion** step to understand the "meaning" of a crime (e.g., mapping "snatching" to "Section 356/379").
    - Implements a **Weighted Keyword Search** algorithm to find the most relevant IPC sections from a local JSON database.
    - Injects top 15 relevant laws into the AI's context for accurate citations.
- **Official Details Support**: structured inputs for Police Station, Officer Rank, FIR Number, etc.

## Directory Structure
- `main.py`: The entry point for the FastAPI application. Handles API routes and LLM interaction.
- `models.py`: Pydantic models defining the data structure for API requests.
- `utils.py`: Contains the logic for loading IPC data, expanding queries, and searching for relevant sections.
- `laws_json/`: Directory containing the `ipc.json` reference file.

## Setup Instructions

### 1. Prerequisites
- Python 3.8+
- A Groq API Key

### 2. Installation
Create a virtual environment and install dependencies:
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the `backend` directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Running the Server
Start the FastAPI development server:
```bash
uvicorn main:app --reload --port 8000
```
The API will be available at `http://127.0.0.1:8000`.
API Docs are available at `http://127.0.0.1:8000/docs`.
