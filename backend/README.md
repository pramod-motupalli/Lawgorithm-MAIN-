# Lawgorithm - Backend API

## Overview

This is the backend service for the **Lawgorithm** application. It provides a RESTful API to generate legally structured FIRs, conduct investigations, and predict court verdicts using advanced RAG and AI Agents.

It is built with **FastAPI** and leverages **Groq (Llama 3.3 70B)** for high-reasoning legal tasks.

## 🧠 Core Intelligence

### 1. Hybrid RAG Engine

Lawgorithm uses a hybrid retrieval system to ensure legal accuracy:

- **Laws DB**: A ChromaDB collection of the Indian Penal Code (IPC), CrPC, and various Indian Acts.
- **Cases DB**: A ChromaDB collection of historical case precedents.
- **Weighted Retrieval**: Combines semantic embeddings (Sentence Transformers) with keyword-based filtering to narrow down relevant sections.

### 2. Multi-Agent Pipeline

- **Legal Evaluator**: Validates if the user input is meaningful or gibberish before processing.
- **Section Guesser**: An agent that identifies potential legal act/section candidates to optimize vector search.
- **Precedent Retrieval Agent**: An autonomous loop that uses tools (function calling) to search the Cases DB, analyze results, and refine queries until 3-5 high-quality precedents are found.
- **Judicial Auditor**: Analyzes the final verdict for fairness and potential demographic bias.

## 🛠 Endpoints

- `POST /api/generate_fir`: Drafts an FIR with retrieved legal context.
- `POST /api/generate_questionnaire`: Creates interrogation questions and simulated answers.
- `POST /api/generate_charge_sheet`: Compiles investigation data into a Section 173 CrPC report.
- `POST /api/predict_verdict`: Uses agentic retrieval to predict outcome and sentencing.
- `POST /api/analyze_fairness`: Audits the verdict for legal consistency and bias.

## 📂 Directory Structure

- `main.py`: Entry point for FastAPI and core endpoint logic.
- `utils.py`: Contains ChromaDB connection logic, semantic search functions, and embedding models.
- `build_laws_chromadb.py`: Utility to ingest legal JSON files into ChromaDB.
- `build_cases_chromadb.py`: Utility to ingest historical case datasets into ChromaDB.
- `models.py`: Pydantic schemas for request/response validation.
- `laws_json/`: Raw dataset of Indian laws.

## 🚀 Setup

### 1. Prerequisites

- Python 3.9+
- Groq API Key

### 2. Installation

```bash
python -m venv venv
source venv/bin/activate  # .\venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 3. Database Initialization

Before running for the first time, you may need to build the vector indexes:

```bash
python build_laws_chromadb.py
python build_cases_chromadb.py
```

### 4. Run

```bash
uvicorn main:app --reload --port 8000
```
