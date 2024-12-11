# Vertex AI Answers Proxy

This application acts as a proxy for the Vertex AI Conversational Search API, adding features such as API key authentication, request logging to Google Cloud Storage (GCS), and enriching answers with metadata from referenced documents.

## Key Features

* **API Key Authentication:** Protects your Vertex AI Answers endpoint with API key based authentication.
* **Request Logging:** Logs all requests and responses to a designated GCS bucket for analysis and auditing.
* **Metadata Enrichment:**  Enriches the responses from Vertex AI Answers by including metadata from the Google Cloud Storage objects referenced in the answer's citations. This provides additional context and information about the source documents.
* **Session Management:** Handles session creation and management for conversational search interactions.

## Deployment to Cloud Run

1. **Prerequisites:**
    *  A Google Cloud Project with the Cloud Run API enabled.
    *  A Google Cloud Storage bucket for logging.
    *  A Vertex AI Search Engine configured for Conversational Search.
    *  An API key for authentication (you can use API Gateway or a similar service to manage your API keys).
    *  gcloud CLI installed and configured.

2. **Build the Docker image:**

```bash
docker build -t vertex-ai-answers-proxy .
```

3. **Push the Docker image to Google Container Registry (GCR):**

```bash
docker tag vertex-ai-answers-proxy gcr.io/<your-project-id>/vertex-ai-answers-proxy
docker push gcr.io/<your-project-id>/vertex-ai-answers-proxy
```
   Replace `<your-project-id>` with your Google Cloud project ID.


4. **Deploy to Cloud Run:**

```bash
gcloud run deploy vertex-ai-answers-proxy \
  --image gcr.io/<your-project-id>/vertex-ai-answers-proxy \
  --region <your-region> \
  --allow-unauthenticated \ # You might want to remove this after testing and implement proper authentication if deploying publicly.  See Authentication Section below.
  --set-env-vars API_KEY=<your-api-key>,GOOGLE_CLOUD_PROJECT=<your-project-id>,GCS_BUCKET=<your-gcs-bucket-name>,LOCATION=<your-location>,VERTEX_AI_SEARCH_ENGINE=<your-engine-id>
```

   Replace the placeholders with your actual values:

    * `<your-region>`: The Cloud Run region (e.g., `us-central1`).
    * `<your-api-key>`:  Your API key.
    * `<your-gcs-bucket-name>`: The name of your GCS bucket.
    * `<your-location>`: The location of your Discovery Engine resources, e.g. "global" or "us-central1".
    * `<your-engine-id>`: Your Vertex AI Conversational Search engine ID.

## Running Locally

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Set environment variables:**

```bash
export API_KEY=<your-api-key>
export GOOGLE_CLOUD_PROJECT=<your-project-id>
export GCS_BUCKET=<your-gcs-bucket-name>
export LOCATION=<your-location> # e.g. "global" or "us-central1"
export VERTEX_AI_SEARCH_ENGINE=<your-engine-id>
```

3. **Run the application:**

```bash
uvicorn app:app --reload
```

## Authentication
By default, the deployment command above sets `--allow-unauthenticated`.  For production, ensure appropriate authentication measures.  One approach is using API Gateway:

1. Create an API Gateway.
2. Create an API config.
3. Create a route.
4. Create an API key.
5. Associate the API key with a service account.
6. Grant the service account the `Cloud Run Invoker` role on your Cloud Run service.  

This setup ensures only requests with valid API keys can access your Cloud Run service. Remove `--allow-unauthenticated` from the deploy command if you're using API Gateway.

##  Code Overview
* `app.py`: Main application file containing the FastAPI app. Handles routing, API key validation, and interaction with the Vertex AI Answers API.
* `model.py`: Defines Pydantic models for request and response validation.
* `Dockerfile`:  Configuration for building the Docker image.
* `requirements.txt`: Lists the project dependencies.
