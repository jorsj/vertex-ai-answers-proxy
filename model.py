from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Source(BaseModel):
    """
    Represents a source of information.

    Attributes:
        reference_id (str): The ID of the reference.
    """
    reference_id: str = Field(..., alias='referenceId')


class Citation(BaseModel):
    """
    Represents a citation within a text.

    Attributes:
        end_index (str): The end index of the citation in the text.
        sources (List[Source]): The sources of the citation.
        start_index (Optional[str]): The start index of the citation in the text.
    """
    end_index: str = Field(..., alias='endIndex')
    sources: List[Source]
    start_index: Optional[str] = Field(None, alias='startIndex')


class DocumentMetadata(BaseModel):
    """
    Represents metadata about a document.

    Attributes:
        document (str): The document identifier.
        uri (str): The URI of the document.
        title (str): The title of the document.
        page_identifier (str): The page identifier within the document.
    """
    document: str
    uri: str
    title: str
    page_identifier: str = Field(..., alias='pageIdentifier')


class ChunkInfo(BaseModel):
    """
    Represents information about a chunk of text.

    Attributes:
        content (str): The text content of the chunk.
        relevance_score (float): The relevance score of the chunk.
        document_metadata (DocumentMetadata): The metadata of the document the chunk belongs to.
    """
    content: str
    relevance_score: float = Field(..., alias='relevanceScore')
    document_metadata: DocumentMetadata = Field(..., alias='documentMetadata')


class Reference(BaseModel):
    """
    Represents a reference to a chunk of information.

    Attributes:
        chunk_info (ChunkInfo): Information about the referenced chunk.
    """
    chunk_info: ChunkInfo = Field(..., alias='chunkInfo')


class Answer(BaseModel):
    """
    Represents an answer to a query.

    Attributes:
        answer_text (str): The text of the answer.
        citations (List[Citation]): Citations supporting the answer.
        references (List[Reference]): References to relevant information chunks.
        related_questions (List[str]): Related questions to the query.
    """
    answer_text: str = Field(..., alias='answerText')
    citations: List[Citation]
    references: List[Reference]
    related_questions: List[str] = Field(..., alias='relatedQuestions')


class Session(BaseModel):
    """
    Represents a user session.

    Attributes:
        name (Optional[str]): The name of the session.
        state (Optional[str]): The state of the session.
        user_pseudo_id (str): The pseudonymized ID of the user.
        start_time (Optional[str]): The start time of the session.
        end_time (Optional[str]): The end time of the session.
    """
    name: Optional[str] = None
    state: Optional[str] = None
    user_pseudo_id: str = Field(alias='userPseudoId')
    start_time: Optional[str] = Field(alias='startTime', default=None)
    end_time: Optional[str] = Field(alias='endTime', default=None)


class Response(BaseModel):
    """
    Represents a response to a request.

    Attributes:
        answer (Optional[Answer]): The answer to the request, if any.
        session (Optional[Session]): Information about the user session.
    """
    answer: Optional[Answer] = None
    session: Optional[Session] = None


class Metadata(BaseModel):
    """
    Represents a key-value pair of metadata.

    Attributes:
        key (str): The key of the metadata.
        value (str): The value of the metadata.
    """
    key: str = None
    value: str = None


class Request(BaseModel):
    """
    Represents a request for information.

    Attributes:
        prompt (Optional[str]): An optional prompt to provide context for the query.
        query (str): The user's query.
        session (Session): Information about the user session.
        language_code (Optional[str]): The language code of the request (default: "es").
        ignore_adversarial_query (Optional[bool]): Whether to ignore adversarial queries (default: True).
        ignore_non_summary_seeking_query (Optional[bool]): Whether to ignore non-summary seeking queries (default: True).
    """
    prompt: Optional[str] = Field(default="")
    query: str
    session: Session
    language_code: Optional[str] = Field(default="es", alias='languageCode')
    ignore_adversarial_query: Optional[bool] = Field(default=True)
    ignore_non_summary_seeking_query: Optional[bool] = Field(default=True)
