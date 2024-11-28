import logging
import os
import re

import uvicorn
import asyncio
import datetime
from fastapi import FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core.client_options import ClientOptions
from proto import Message
from google.protobuf.json_format import MessageToJson, MessageToDict
from model import Request
from functools import lru_cache

API_KEY = os.environ["API_KEY"]
PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
BUCKET_NAME = os.environ["GCS_BUCKET"]
LOCATION = os.environ.get("LOCATION", "global")

storage_client = storage.Client()
logging_bucket = storage_client.bucket(BUCKET_NAME)

client_options = (
    ClientOptions(api_endpoint=f"{LOCATION}-discoveryengine.googleapis.com")
    if LOCATION != "global"
    else None
)

conversational_client = discoveryengine.ConversationalSearchServiceClient(
    client_options=client_options
)

app = FastAPI(docs_url=None, redoc_url=None)
api_key_header = APIKeyHeader(name="X-API-Key")


async def write_to_gcs(answer, session_name: str):
    """
    Asynchronously writes a payload to a GCS bucket.

    Args:
        :param payload:
        :param session_name:
    """

    json_payload = MessageToJson(
        Message.pb(answer),
        ensure_ascii=False,
    )

    filename = f"vertexai-answers-proxy/logs/{session_name}/{datetime.datetime.now().isoformat()}.json"

    try:
        blob = logging_bucket.blob(filename)
        await asyncio.to_thread(blob.upload_from_string, str(json_payload))
        logging.info(f"Payload written to gs://{BUCKET_NAME}/{filename}")
    except Exception as e:
        logging.error(f"Error writing to GCS: {e}")


def create_session(user_pseudo_id: str, engine_id: str) -> str:
    """Creates a new session in the specified data store.

    This function sends a POST request to the Agent Builder API to create
    a new session associated with the provided user pseudo ID and data store.

    Args:
        user_pseudo_id: The unique identifier of the user.
        engine_id: The name of the data store to create the session in.

    Returns:
        The name of the newly created session.

    Raises:
        requests.exceptions.RequestException: If the request to the Discovery Engine API fails.
    """
    session = conversational_client.create_session(
        # The full resource name of the engine
        parent=f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/engines/{engine_id}",
        session=discoveryengine.Session(user_pseudo_id=user_pseudo_id),
    )
    return session.name


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
    if api_key_header in [API_KEY]:
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


@lru_cache(maxsize=None)
def get_metadata(uri: str) -> dict[str, str]:
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
    try:
        bucket_name, blob_name = parse_gcs_uri(uri)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.get_blob(blob_name)
        return blob.metadata
    except Exception as e:
        logging.error(f"Error obtaining metadata for {uri}: {e}")
    return None


def enrich_answer_with_metadata(answer):
    """Enriches an answer message with object metadata from each referenced chunk's URI.

    This function takes a protobuf answer message, converts it to a dictionary,
    and then adds object metadata to each reference's chunk information.  The
    metadata is retrieved using the `get_metadata` function, based on the URI
    specified in the document metadata of each chunk.

    Args:
        answer: A protobuf message representing the answer.

    Returns:
        A dictionary representation of the enriched answer message, including
        the added object metadata within each reference's chunkInfo.

    Raises:
        Any exceptions raised by `MessageToDict`, `Message.pb`, or `get_metadata` will be propagated.
    """
    answer_dict = MessageToDict(
        Message.pb(answer),
    )
    try:
        for reference in answer_dict["answer"]["references"]:
            uri = reference["chunkInfo"]["documentMetadata"]["uri"]
            reference["chunkInfo"]["objectMetadata"] = get_metadata(uri)
    except KeyError as e:
        logging.info(f"Answer does not contain any references: {e}")
    return answer_dict


@app.post("/answer/{engine_id}", response_model_exclude_none=True)
async def answer(
    engine_id: str, request: Request, api_key: str = Security(get_api_key)
) -> JSONResponse:
    """
    Answers a user's query using Vertex AI Answers API.

    This endpoint receives a user's query and returns an answer generated by Vertex AI Answers,
    along with related information like citations and related questions.

    Args:
        engine_id: The engine to query against.
        request: The incoming request containing the user's query and other parameters.
        api_key: The API key for authentication.

    Returns:
        A Response object containing the answer generated by Google Discovery Engine.

    Raises:
        HTTPException: If an error occurs during the API call or response processing.
    """
    if request.session.name is None:
        session_name = create_session(request.session.user_pseudo_id, engine_id)
    else:
        session_name = request.session.name

    serving_config = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/engines/{engine_id}/servingConfigs/default_serving_config"

    query_understanding_spec = discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec(
        query_rephraser_spec=discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryRephraserSpec(
            disable=request.disable_query_rephraser,
            max_rephrase_steps=request.max_rephrase_steps,
        ),
    )

    answer_generation_spec = discoveryengine.AnswerQueryRequest.AnswerGenerationSpec(
        ignore_adversarial_query=request.ignore_adversarial_query,
        ignore_non_answer_seeking_query=request.ignore_non_answer_seeking_query,
        ignore_low_relevant_content=request.ignore_low_relevant_content,
        model_spec=discoveryengine.AnswerQueryRequest.AnswerGenerationSpec.ModelSpec(
            model_version=request.model_version,
        ),
        prompt_spec=discoveryengine.AnswerQueryRequest.AnswerGenerationSpec.PromptSpec(
            preamble=request.preamble,
        ),
        include_citations=request.include_citations,
        answer_language_code=request.language_code,
    )

    search_spec = discoveryengine.AnswerQueryRequest.SearchSpec(
        search_params=discoveryengine.AnswerQueryRequest.SearchSpec.SearchParams(
            max_return_results=request.max_return_results,
        )
    )

    request = discoveryengine.AnswerQueryRequest(
        serving_config=serving_config,
        query=discoveryengine.Query(text=request.query),
        session=session_name,
        query_understanding_spec=query_understanding_spec,
        answer_generation_spec=answer_generation_spec,
        search_spec=search_spec,
    )

    answer = conversational_client.answer_query(request)

    asyncio.create_task(
        write_to_gcs(answer, session_name)
    )  # Non-blocking task creation

    answer = enrich_answer_with_metadata(answer)

    return JSONResponse(content=answer)


if __name__ == "__main__":
    port = os.environ.get("PORT", 8000)
    uvicorn.run(app, host="0.0.0.0", port=port)
