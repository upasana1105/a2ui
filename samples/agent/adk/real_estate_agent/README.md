# Real Estate Agent Setup Guide

This guide provides instructions for setting up and running the Real Estate Agent application.

## Prerequisites

-   Python 3.12 or higher
-   Node.js and NPM
-   Google Cloud Project with Vertex AI and Google Search grounding enabled
-   Google Maps API Key

## Environment Setup

1.  **Clone the repository and navigate to the project root.**
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
3.  **Install local dependencies in editable mode:**
    ```bash
    pip install -e a2ui_project/a2a_agents/python/a2ui_extension
    cd a2ui_project/samples/agent/adk/real_estate_agent
    pip install -e .
    ```

## Configuration

Ensure you have a `.env` file in the `real_estate_agent` directory or the project root with the following:

-   `GOOGLE_CLOUD_PROJECT`: Your project ID (e.g., `uppdemos`)
-   `GOOGLE_MAPS_API_KEY`: Your API key for Google Maps
-   `GOOGLE_GENAI_USE_VERTEXAI`: Set to `true`

## Launch instructions

### 1. Start the Backend Agent
```bash
python __main__.py
```
The agent will be available at `http://localhost:10003`.

### 2. Start the Frontend Shell
Navigate to `a2ui_project/samples/client/lit/shell` and run:
```bash
npx vite dev --port 5180
```
Then open `http://localhost:5180/?app=real_estate` in your browser.

## Testing

Enter a query like "Find me houses in Palo Alto" to see the agent retrieve and render property listings.
