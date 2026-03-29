"""Chatbot API endpoints — delegates to the chatbot engine for intent handling."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from backend.models.schemas import APIResponse, ChatbotRequest, ChatbotResponse
from backend.services.chatbot_engine import SAMPLE_SUGGESTIONS, process_query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chatbot", tags=["chatbot"])


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/query", response_model=APIResponse[ChatbotResponse])
async def chatbot_query(req: ChatbotRequest) -> APIResponse[ChatbotResponse]:
    """Process a natural-language query about flight delays.

    Accepts ``{"message": "..."}`` and returns a structured response with
    an answer string, optional data rows, and a chart-type hint.
    """
    result = process_query(req.message)
    return APIResponse(
        data=ChatbotResponse(
            answer=result.answer,
            data=result.data,
            chart_type=result.chart_type,
        )
    )


@router.get("/suggestions", response_model=APIResponse[list[str]])
async def chatbot_suggestions() -> APIResponse[list[str]]:
    """Return a list of sample questions the user can ask."""
    return APIResponse(data=SAMPLE_SUGGESTIONS)
