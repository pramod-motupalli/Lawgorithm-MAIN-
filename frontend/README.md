# Lawgorithm - Frontend UI

## Overview
This is the frontend user interface for the **Lawgorithm** application. It is a modern, responsive web application designed with a professional "Legal/Official" aesthetic to assist officers in drafting FIRs.

It is built with **React**, **Vite**, and **Tailwind CSS (v4)**.

## Key Features
- **Official Styling**: Custom color palette inspired by the Andhra Pradesh Police (Khaki `#dccba0`, Navy `#1a3c6e`, Red `#d32f2f`).
- **Structured Inputs**:
    - Dedicated "Official Details" section for Station Name, FIR Number, IO Name, etc.
    - Sections for Complainant, Accused, and Incident details.
- **Smart Preview & Print**:
    - **Clean Print Mode**: Removes UI elements (buttons, backgrounds) and formats the FIR as a clean, black-and-white legal document for physical printing.
    - **Live Preview**: Shows the generated FIR text with bold headings and structured layout.
- **Interactive Loading**: Provides feedback while the AI processes the legal context.

## Setup Instructions

### 1. Prerequisites
- Node.js (v16+)
- npm

### 2. Installation
Install project dependencies:
```bash
npm install
```

### 3. Running the App
Start the development server:
```bash
npm run dev
```
The application will launch at `http://localhost:5173`.

## Configuration
The frontend is configured to talk to the backend at `http://127.0.0.1:8000` by default. If your backend runs on a different port, update the API call in `src/App.jsx`.
