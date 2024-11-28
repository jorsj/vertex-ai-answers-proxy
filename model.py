from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    class Config:
        alias_generator = to_camel
        populate_by_name = True


class Session(CamelModel):
    """
    Represents a user session.

    Attributes:
        name (str, optional): The name of the session.
        state (str, optional): The state of the session.
        user_pseudo_id (str, optional): The pseudonymized ID of the user.
        start_time (str, optional): The start time of the session.
        end_time (str, optional): The end time of the session.
    """

    name: Optional[str] = None
    state: Optional[str] = None
    user_pseudo_id: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class Request(CamelModel):
    """Represents a request for information retrieval.

    Attributes:
        preamble (Optional[str]): An optional introductory text to provide context for the query. Defaults to None.
        query (str): The main query string.
        session (Optional[Session]): An optional session object for maintaining context across multiple requests. Defaults to None.
        language_code (Optional[str]): The language code for the query. Defaults to "es" (Spanish).
        ignore_adversarial_query (Optional[bool]): Whether to ignore adversarial queries. Defaults to False.
        ignore_non_answer_seeking_query (Optional[bool]): Whether to ignore queries that are not seeking answers. Defaults to False.
        ignore_low_relevant_content (Optional[bool]): Whether to ignore content with low relevance. Defaults to False.
        disable_query_rephraser (Optional[bool]): Whether to disable query rephrasing. Defaults to False.
        max_rephrase_steps (Optional[int]): The maximum number of rephrasing steps allowed. Defaults to 5.
        model_version (Optional[str]): The version of the model to use. Defaults to "gemini-1.5-flash-001/answer_gen/v2".
        include_citations (Optional[bool]): Whether to include citations in the response. Defaults to True.
        max_return_results (Optional[int]): The maximum number of results to return. Defaults to 10.
    """

    preamble: Optional[str] = None
    query: str
    session: Optional[Session] = None
    language_code: Optional[str] = "es"
    ignore_adversarial_query: Optional[bool] = False
    ignore_non_answer_seeking_query: Optional[bool] = False
    ignore_low_relevant_content: Optional[bool] = False
    disable_query_rephraser: Optional[bool] = False
    max_rephrase_steps: Optional[int] = 5
    model_version: Optional[str] = "gemini-1.5-flash-001/answer_gen/v2"
    include_citations: Optional[bool] = True
    max_return_results: Optional[int] = 10
