# Lawgorithm - Frontend UI

## Overview

This is the frontend user interface for the **Lawgorithm** application. It is a modern, responsive web application designed with a professional "Legal/Official" aesthetic to assist officers in drafting and analyzing legal cases.

It is built with **React**, **Vite**, and **Tailwind CSS (v4)**.

## 🏛 Legal Design System

The UI utilizes a curated color palette and typography inspired by modern judicial interfaces:

- **Khaki (`#dccba0`)**: Base official color.
- **Navy (`#1a3c6e`)**: Primary brand color for headings and buttons.
- **Cream (`#f4f0e6`)**: Background for better readability of legal text.

## ⚖️ 4-Step Legal Wizard

The application guides users through a structured legal process:

1.  **FIR Interface**: A comprehensive form for incident, complainant, and accused details.
2.  **Investigation Hub**: A dynamic questionnaire where AI generates interrogation questions based on the FIR.
3.  **Charge Sheet Preview**: A formal view of the Section 173 CrPC report generated from the case context.
4.  **Judicial Dashboard**: Displays the predicted verdict, sentencing, and a fairness analysis report.

## 🛠 Features

- **Clean Print Mode**: Specialized CSS for printing generated FIRs and Charge Sheets as standard white-and-black legal documents.
- **Context-Aware Navigation**: A progress indicator to track where the officer is in the legal pipeline.
- **Real-time Pre-validation**: Detects gibberish or insufficient case descriptions before API submission.

## 🚀 Setup Instructions

### 1. Prerequisites

- Node.js (v18+)
- npm

### 2. Installation

```bash
npm install
```

### 3. Running the App

```bash
npm run dev
```

The application will launch at `http://localhost:5173`.

## ⚙️ Configuration

The frontend communicates with the backend via Axios. The base URL is configured in `src/App.jsx` and points to `http://127.0.0.1:8000` by default.
