from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class Source(BaseModel):
    """
    Represents a source of information for a citation.

    Attributes:
        reference_id (str, optional): The ID of the reference.
    """

    reference_id: Optional[str] = Field(None, alias="referenceId")


class Citation(BaseModel):
    """
    Represents a citation within a text.

    Attributes:
        end_index (str, optional): The end index of the citation in the text.
        sources (List[Source], optional): The sources of the citation.
        start_index (str, optional): The start index of the citation in the text.
    """

    end_index: Optional[str] = Field(..., alias="endIndex")
    sources: Optional[List[Source]] = None
    start_index: Optional[str] = Field(None, alias="startIndex")


class DocumentMetadata(BaseModel):
    """
    Represents metadata about a document.

    Attributes:
        document (str, optional): The document identifier.
        uri (str, optional): The URI of the document.
        title (str, optional): The title of the document.
        page_identifier (str, optional): The page identifier within the document.
    """

    document: Optional[str] = None
    uri: Optional[str] = None
    title: Optional[str] = None
    page_identifier: Optional[str] = Field(None, alias="pageIdentifier")


class ChunkInfo(BaseModel):
    """
    Represents information about a chunk of text.

    Attributes:
        content (str, optional): The text content of the chunk.
        relevance_score (float, optional): The relevance score of the chunk.
        document_metadata (DocumentMetadata, optional): The metadata of the document the chunk belongs to.
    """

    content: Optional[str] = None
    relevance_score: Optional[float] = Field(None, alias="relevanceScore")
    document_metadata: Optional[DocumentMetadata] = Field(None, alias="documentMetadata")


class Reference(BaseModel):
    """
    Represents a reference to a chunk of information.

    Attributes:
        chunk_info (ChunkInfo, optional): Information about the referenced chunk.
    """

    chunk_info: Optional[ChunkInfo] = Field(None, alias="chunkInfo")


class Answer(BaseModel):
    """
    Represents an answer to a query.

    Attributes:
        answer_text (str, optional): The text of the answer.
        citations (List[Citation], optional): Citations supporting the answer.
        references (List[Reference], optional): References to relevant information chunks.
        related_questions (List[str], optional): Related questions to the query.
    """

    answer_text: Optional[str] = Field(None, alias="answerText")
    citations: Optional[List[Citation]] = None
    references: Optional[List[Reference]] = None
    related_questions: Optional[List[str]] = Field(None, alias="relatedQuestions")


class Session(BaseModel):
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
    user_pseudo_id: Optional[str] = Field(None, alias="userPseudoId")
    start_time: Optional[str] = Field(None, alias="startTime")
    end_time: Optional[str] = Field(None, alias="endTime")


class Response(BaseModel):
    """
    Represents a response to a request.

    Attributes:
        answer (Answer, optional): The answer to the request, if any.
        session (Session, optional): Information about the user session.
    """

    answer: Optional[Answer] = None
    session: Optional[Session] = None


class Metadata(BaseModel):
    """
    Represents a key-value pair of metadata.

    Attributes:
        key (str, optional): The key of the metadata.
        value (str, optional): The value of the metadata.
    """

    key: Optional[str] = None
    value: Optional[str] = None


class Request(BaseModel):
    """
    Represents a request for information.

    Attributes:
        preamble (str, optional): An optional prompt to provide context for the query.
        query (str): The user's query.
        session (Session, optional): Information about the user session.
        language_code (str, optional): The language code of the request (default: "es").
        ignore_adversarial_query (bool, optional): Whether to ignore adversarial queries (default: True).
        ignore_non_summary_seeking_query (bool, optional): Whether to ignore non-summary seeking queries (default: True).
    """

    preamble: Optional[str] = Field(None)
    query: str
    session: Optional[Session] = None
    language_code: Optional[str] = Field("es", alias="languageCode")
    ignore_adversarial_query: Optional[bool] = Field(True)
    ignore_non_summary_seeking_query: Optional[bool] = Field(True)
