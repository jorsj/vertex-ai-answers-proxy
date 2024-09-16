## Vertex AI Answers Proxy API

This repository contains a simple FastAPI-based proxy API for interacting with Google Cloud's Vertex AI Answers API. It provides an additional layer of security by requiring an API key for authentication and allows for easier integration with applications that need to access Vertex AI Answers functionality.

### Features

* Secure access to Vertex AI Answers API using API keys.
* Simplified request and response handling.
* Easy deployment to Cloud Run using the provided Dockerfile.

### Requirements

* Python 3.12
* Virtual environment (recommended)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/your-username/vertex-ai-answers-proxy.git
cd vertex-ai-answers-proxy
```

2. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Set the required environment variables:

* `GOOGLE_CLOUD_PROJECT`: Your Google Cloud project ID.
* `API_KEY`: The API key that will be used for authentication.

You can set these variables directly in your terminal session or add them to a `.env` file and load them using `source .env`.

### Usage

The API exposes a single endpoint:

* **POST /answer/{data_store}**: Sends a query to the Vertex AI Answers API and returns the response.

**Request body:**

The request body should be a JSON object conforming to the `Request` model defined in `model.py`. For example:

```json
{
"prompt": "What is the capital of France?",
"query": "capital of France",
"session": {
"userPseudoId": "user123"
},
"languageCode": "en"
}
```

**Headers:**

The request must include the `X-API-Key` header with a valid API key.

**Response:**

The response will be a JSON object conforming to the `Response` model defined in `model.py`.

### Deployment to Cloud Run

1. Build the Docker image:

```bash
docker build -t vertex-ai-answers-proxy .
```

2. Push the image to Google Container Registry:

```bash
docker tag vertex-ai-answers-proxy gcr.io/<your-project-id>/vertex-ai-answers-proxy
docker push gcr.io/<your-project-id>/vertex-ai-answers-proxy
```

3. Deploy to Cloud Run:

```bash
gcloud run deploy vertex-ai-answers-proxy \
--image gcr.io/<your-project-id>/vertex-ai-answers-proxy \
--region <your-region> \
--allow-unauthenticated
```

Replace `<your-project-id>`, `<your-region>`, and other placeholders with your actual values.

### Contributing

Contributions are welcome! If you find any issues or have suggestions for improvement, feel free to open an issue or submit a pull request.