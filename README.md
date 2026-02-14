

# Digital Fortune Cookie Backend (Flask + Render)

## What This Backend Does

This backend is a small Flask API deployed on Render that generates “fortune cookie” responses using the Dedalus (OpenAI-compatible) API. It exposes a JSON API that a frontend can call to generate fortunes based on user input.

## Endpoints

GET /health
Health check endpoint to confirm the server is running.

Response:

{
  "ok": true
}

POST /api/fortune
Generates a fortune cookie response.

Request body (JSON):

{
  "question": "Should I go outside today?",
  "mood": "cryptic"
}

## Parameters:

question (string, required): The user’s question or thought (max 400 characters)

mood (string, optional): One of hopeful, cryptic, playful, grounding, bold. If omitted or invalid, a mood is selected automatically.

Response (JSON):

{
  "fortune": "A door awaits your gentle push; beyond it lies a world of whispers and wonders.",
  "suggestion": "Step outside and take a breath.",
  "lucky": "purple",
  "mood": "cryptic",
  "symbol": "Door",
  "source": "dedalus"
}

If the Dedalus API fails or no API key is provided, the backend returns a safe fallback response with source: "fallback" and additional debugging fields.

## How the Frontend Communicates With the Backend

The frontend communicates with this backend using JavaScript fetch() calls.

When the user clicks “Crack cookie”, the frontend sends a POST request to:

/api/fortune

The frontend sends:

question from a text input

mood from a dropdown (optional)

The frontend uses the response to display:

fortune as the main message

suggestion as a secondary prompt

symbol as a visual icon

mood as metadata

The frontend also handles error states such as empty input, backend downtime, or invalid responses.

## How to Set Up and Run the Backend Locally

Clone the repository and create a virtual environment:

git clone <YOUR_BACKEND_REPO_URL>
cd <YOUR_BACKEND_REPO_FOLDER>
python -m venv .venv

Activate the virtual environment:

Windows (PowerShell)

.venv\Scripts\activate

macOS / Linux

source .venv/bin/activate

Install dependencies:

pip install -r requirements.txt
Environment Variables

This backend requires Dedalus credentials, provided via environment variables.

Windows (PowerShell)

$env:DEDALUS_API_KEY="YOUR_KEY_HERE"
$env:DEDALUS_BASE_URL="https://api.dedaluslabs.ai"
$env:DEDALUS_MODEL="openai/gpt-4o-mini"

macOS / Linux

export DEDALUS_API_KEY="YOUR_KEY_HERE"
export DEDALUS_BASE_URL="https://api.dedaluslabs.ai"
export DEDALUS_MODEL="openai/gpt-4o-mini"

Run the server locally: 


python app.py

Visit: http://127.0.0.1:5000/health


## Authentication and Secrets

This project uses an API key to access the Dedalus API.

API keys are stored only on the backend using environment variables.

The frontend does not include or expose any API keys.

In production, environment variables are configured in the Render dashboard.

## Required environment variables:

DEDALUS_API_KEY (required)

DEDALUS_BASE_URL (optional, defaults to https://api.dedaluslabs.ai)

DEDALUS_MODEL (optional, defaults to openai/gpt-4o-mini)

## AI Models used
Dedalus, base model GPT 4o mini

## Prompt History
I want to create something where you can enter in text, and a fortune is made using a backend. How would i set this up in render?
Create the app.py code for me and the neccesary files I need to create this fortune cookie feature
The front end should be a part of my existing website, how would i implement this? I want it to be a card under my projects so far: "inserted my html for that page for context"
Give me the updated js code for the feature on my website to call my backend