
# Project Setup & Deployment Guide

This document provides a comprehensive guide to setting up the CodeIQ project for local development and deploying it to a live production environment. It also details the key challenges faced during the process and the solutions that were implemented.

## Part 1: Local Development Setup

The entire application is containerized using Docker and Docker Compose, ensuring a consistent and easy-to-manage development environment.

### Prerequisites

* **Docker Desktop:** Must be installed and running.
* **Git:** For cloning the repository.
* **Google Gemini API Key:** A valid API key is required for the AI core to function.

### Step-by-Step Instructions

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/Virtuoso633/CodeQualityAgent.git](https://github.com/Virtuoso633/CodeQualityAgent.git)
    cd CodeQualityAgent
    ```

2.  **Configure Environment Variables:**
    * The project uses a `.env` file for managing secrets. Make a copy of the example file:
      ```bash
      cp .env.example .env
      ```
    * Open the newly created `.env` file and populate the `GEMINI_API_KEY` with your key.
      ```
      GEMINI_API_KEY=your_secret_gemini_api_key_here
      ```
    * The `GITHUB_TOKEN` is optional but required for analyzing private GitHub repositories.

3.  **Build and Run the Application:**
    * The `docker-compose.yml` file is located in the `web/` directory.
    * Execute the following command from the project root:
      ```bash
      docker-compose -f web/docker-compose.yml up --build
      ```
    * The `--build` flag is necessary on the first run. For subsequent runs, `docker-compose up` is sufficient. This command starts two services:
        * `codeiq-backend`: The FastAPI server.
        * `codeiq-frontend`: The Streamlit server.
    * The frontend is configured in this file to talk to the backend using Docker's internal network: `API_BASE_URL=http://codeiq-backend:8000`.

4.  **Accessing the Services:**
    * **Frontend Dashboard:** `http://localhost:8501`
    * **Backend API (Swagger UI):** `http://localhost:8000/docs`

5.  **Stopping the Application:**
    * Press `Ctrl + C` in the terminal where `docker-compose` is running.
    * To remove the containers and network, run `docker-compose -f web/docker-compose.yml down`.

## Part 2: Cloud Deployment

The application is deployed using a modern, robust, and free-tier-friendly architecture.

* **Backend (FastAPI):** Deployed as a Docker container on **Koyeb**.
* **Frontend (Streamlit):** Deployed on **Streamlit Community Cloud**.

### Backend Deployment (Koyeb)

1.  **Prerequisites:** A Koyeb account connected to your GitHub.
2.  **Deployment Steps:**
    * In the Koyeb dashboard, create a new App and connect the GitHub repository.
    * In the service configuration, select the **Dockerfile** builder.
    * **Crucially, override the "Dockerfile location"** to point to `./web/backend/Dockerfile`.
    * Set the **Instance** to "Free Nano" and the **Port** to `8080` (as exposed in the Dockerfile).
    * Configure the **Health Check** path to `/health`.
    * Under **Environment Variables**, add a **Secret** named `GEMINI_API_KEY` and provide your key.
    * Deploy the service. Once live, copy the public URL (e.g., `https://your-backend-url.koyeb.app`).

### Frontend Deployment (Streamlit Community Cloud)

1.  **Prerequisites:** A Streamlit Community Cloud account connected to your GitHub.
2.  **Deployment Steps:**
    * In the Streamlit dashboard, create a "New app".
    * Select the correct GitHub repository and branch.
    * Set the **"Main file path"** to `web/frontend/streamlit_app.py`.
    * In the **"Advanced settings..."**, go to the **"Secrets"** section.
    * Paste the following, replacing the URL with your **live Koyeb backend URL**:
      ```toml
      API_BASE_URL = "[https://your-backend-url.koyeb.app](https://your-backend-url.koyeb.app)"
      ```
    * Deploy the app.

## Part 3: Key Challenges & Debugging Workflow

This project involved a significant amount of debugging to connect the decoupled services. Here is a summary of the key challenges and their solutions.

### 1. Challenge: Vercel Incompatibility
* **Problem:** The initial plan was to deploy the Streamlit frontend to Vercel. This failed.
* **Diagnosis:** Vercel is designed for stateless serverless functions. Streamlit is a stateful, long-running server that requires a persistent WebSocket connection, which is incompatible with Vercel's architecture.
* **Solution:** We pivoted to the correct platform: **Streamlit Community Cloud**, which is purpose-built for hosting Streamlit applications.

### 2. Challenge: Cloud Memory Crashes
* **Problem:** The deployed backend on Koyeb was stuck in a crash-restart loop. The logs showed `SIGKILL! Perhaps out of memory?`
* **Diagnosis:** The `gunicorn` server was configured to run with 4 workers. The combined memory usage of four separate application instances (each loading heavy AI libraries) was exceeding the RAM limit of Koyeb's "Free Nano" instance.
* **Solution:** The `CMD` in the `web/backend/Dockerfile` was changed from `-w 4` (4 workers) to **`-w 1`** (1 worker). This drastically reduced the memory footprint and allowed the application to run stably.

### 3. Challenge: The "CORS Paradox" (Browser Fails, `curl` Works)
* **Problem:** After deployment, the live frontend failed with an "Analysis Failed" error. `curl` commands to the backend worked perfectly, but requests from the Streamlit app failed. The backend logs showed *no incoming traffic* from Streamlit.
* **Diagnosis:** This is a classic **CORS (Cross-Origin Resource Sharing)** issue. `curl` is not a browser, so it ignores CORS policies. The Streamlit app's request *is* subject to these policies. The Koyeb backend was rejecting the request from the `streamlit.app` domain because it was not on its "allowed origins" list.
* **Solution:** The FastAPI backend (`web/backend/main.py`) was updated with `CORSMiddleware` to explicitly allow requests from all origins (`allow_origins=["*"]`), solving the connection block.

### 4. Challenge: Local `secrets.toml` Overriding Cloud Secrets
* **Problem:** Even after setting the correct `API_BASE_URL` in the Streamlit Cloud dashboard, the deployed app *still* wasn't working and showed the "Analysis Failed" error.
* **Debug Technique:** We added temporary debug code (`st.write(st.secrets['API_BASE_URL'])`) to the Streamlit app's UI. This revealed the app was still loading the *local Docker URL* (`http://codeiq-backend:8000`).
* **Solution:** We discovered a `secrets.toml` file (used for local testing) had been accidentally committed to the GitHub repository. Streamlit Cloud **prioritizes this file over dashboard secrets**. The fix was to:
    1.  Delete the file from the repo: `git rm web/frontend/.streamlit/secrets.toml`.
    2.  Add `.streamlit/` and `web/frontend/.streamlit/` to the root `.gitignore` file.
    3.  `git push` the changes. This forced Streamlit Cloud to fall back to using the (correct) secrets from its dashboard.

### 5. Challenge: The Final Bug (Wrong URL in Secrets)
* **Problem:** After fixing the `secrets.toml` override, the app *still* showed the wrong Docker URL.
* **Diagnosis:** The user had fixed the *override* issue but had not yet corrected the value in the **Streamlit Cloud dashboard secret**. The value in the dashboard was *also* the local Docker URL.
* **Solution:** The final step was to go into the Streamlit Cloud dashboard **Settings > Secrets** and update the `API_BASE_URL` secret to the correct, public Koyeb URL: `https:// xenogeneic-enriqueta-virtuoso633-787cfce7.koyeb.app`.