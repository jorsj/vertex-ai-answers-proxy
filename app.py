import logging
import os
import re

import google.auth.transport.requests
import requests
import uvicorn
from fastapi import FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from google.auth import default
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from model import Request, Metadata, Response

creds, _ = default()
auth_req = google.auth.transport.requests.Request()

api_keys = [os.environ["API_KEY"]]

project = os.environ["GOOGLE_CLOUD_PROJECT"]

storage_client = storage.Client()

app = FastAPI(docs_url=None, redoc_url=None)
api_key_header = APIKeyHeader(name="X-API-Key")


def create_session(user_pseudo_id: str, data_store: str) -> str:
    """Creates a new session in the specified data store.

    This function sends a POST request to the Agent Builder API to create
    a new session associated with the provided user pseudo ID and data store.

    Args:
        user_pseudo_id: The unique identifier of the user.
        data_store: The name of the data store to create the session in.

    Returns:
        The name of the newly created session.

    Raises:
        requests.exceptions.RequestException: If the request to the Discovery Engine API fails.
    """
    creds.refresh(auth_req)
    payload = {
        "url": f"https://discoveryengine.googleapis.com/v1alpha/projects/{project}/locations/global/collections/default_collection/dataStores/{data_store}/sessions",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {creds.token}"
        },
        "json": {"user_pseudo_id": user_pseudo_id}
    }
    session = make_api_call(**payload)
    return session.json()["name"]


def parse_gcs_uri(uri: str) -> tuple[str, str]:
    """Parses a Google Cloud Storage URI.

    Args:
        uri: The Google Cloud Storage URI to parse.

    Returns:
        A tuple containing the bucket name and object name.

    Raises:
        ValueError: If the URI is not a valid Google Cloud Storage URI.
    """

    match = re.match(r"^gs://(?P<bucket>[^/]+)/(?P<name>.*)$", uri)
    if not match:
        raise ValueError("Invalid Google Cloud Storage URI: {}".format(uri))
    return match.group("bucket"), match.group("name")


def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    """Validates an API key provided in a request header.

    Args:
        api_key_header: The API key value extracted from the request header
                        using the 'api_key_header' Security dependency.

    Returns:
        The validated API key.

    Raises:
        HTTPException: If the provided API key is invalid or missing, with a
                       status code of 401 (Unauthorized).
    """
    if api_key_header in api_keys:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )


@app.get("/healthcheck")
async def healthcheck() -> str:
    """
    Provides a simple health check endpoint.

    Returns:
        str: The string "OK" to signal operational status.
    """
    return "OK"


def make_api_call(*args, **kwargs):
    """
    Makes an API call using the 'requests' library, handling credential
    refresh if necessary.

    This function abstracts the process of making API calls, ensuring
    that credentials are valid before attempting the request. If the
    credentials are expired but a refresh token is available, the
    function will attempt to refresh them.

    Args:
        *args: Variable length argument list passed directly to
               `requests.post()`.
        **kwargs: Arbitrary keyword arguments passed directly to
                  `requests.post()`.

    Returns:
        requests.Response: The response object from `requests.post()`
                           if the API call was successful.
        None: If the credentials are invalid and cannot be refreshed.
    """
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(auth_req)
        else:
            # Handle the case where credentials are completely invalid
            # (e.g., the user revoked access)
            logging.error("Credentials are invalid and cannot be refreshed.")
            return
    return requests.post(*args, **kwargs)


def get_metadata(uri: str) -> list[Metadata]:
    """
    Extracts metadata from a Google Cloud Storage object.

    Args:
        uri: A Google Cloud Storage URI in the format "gs://bucket_name/object_name".

    Returns:
        A list of Metadata objects representing the object's metadata.

    Raises:
        ValueError: If the provided URI is not a valid Google Cloud Storage URI.
        GoogleCloudError: If there is an error communicating with the Google Cloud Storage service.
    """
    metadata = []
    try:
        bucket_name, blob_name = parse_gcs_uri(uri)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.get_blob(blob_name)
        for key, value in zip(blob.metadata.keys(), blob.metadata.values()):
            metadata.append(Metadata(key=key, value=value))
        return metadata
    except ValueError as e:
        logging.error(f"Error: Invalid Google Cloud Storage URI: {e}")
    except GoogleCloudError as e:
        logging.error(f"Error communicating with Google Cloud Storage: {e}")


@app.post("/answer/{data_store}", response_model_exclude_none=True)
async def answer(
        data_store: str, request: Request, api_key: str = Security(get_api_key)
) -> Response:
    """
    Answers a user's query using Vertex AI Answers API.

    This endpoint receives a user's query and returns an answer generated by Vertex AI Answers,
    along with related information like citations and related questions.

    Args:
        data_store: The data store to query against.
        request: The incoming request containing the user's query and other parameters.
        api_key: The API key for authentication.

    Returns:
        A Response object containing the answer generated by Google Discovery Engine.

    Raises:
        HTTPException: If an error occurs during the API call or response processing.
    """
    if request.session.name is None:
        session = create_session(request.session.user_pseudo_id, data_store)
    else:
        session = request.session.name
    payload = {
        "url": f"https://discoveryengine.googleapis.com/v1alpha/projects/{project}/locations/global/collections/default_collection/dataStores/{data_store}/servingConfigs/default_search:answer",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {creds.token}"
        },
        "json": {
            "query": {"text": request.query},
            "session": session,
            "safetySpec": {
                "enable": False,
            },
            "relatedQuestionsSpec": {
                "enable": True,
            },
            "queryUnderstandingSpec": {
                "queryClassificationSpec": {
                    "types": ["ADVERSARIAL_QUERY", "NON_ANSWER_SEEKING_QUERY"],
                },
                "queryRephraserSpec": {
                    "disable": False,
                    "maxRephraseSteps": 5,
                },
            },
            "searchSpec": {
                "searchParams": {
                    "maxReturnResults": 10,
                },
            },
            "answerGenerationSpec": {
                "includeCitations": True,
                "answerLanguageCode": request.language_code,
                "modelSpec": {
                    "modelVersion": "preview",
                },
                "promptSpec": {"preamble": request.prompt},
                "ignoreAdversarialQuery": True,
                "ignoreNonAnswerSeekingQuery": False,
            },
            "groundingSpec": {
                "filterLowGroundingAnswer": True,
            }
        }
    }
    response = make_api_call(**payload)
    response = Response.model_validate_json(response.text, strict=False)
    return response


if __name__ == "__main__":
    port = int(os.environ["PORT"])
    uvicorn.run(app, host="0.0.0.0", port=port)
