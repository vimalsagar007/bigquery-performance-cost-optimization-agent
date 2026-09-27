from fastapi import APIRouter, HTTPException
from app.models.requests import ChatRequest
from app.models.responses import ChatResponse
from app.agents.optimizer_agent import optimizer_agent

chat_router = APIRouter()


@chat_router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """
    POST /chat
    Conversational agent endpoint supporting natural language prompts such as:
    - "Find my most expensive queries in the last 7 days."
    - "Why is this query expensive?"
    - "How can I reduce bytes processed?"
    - "Which queries are consuming the most slots?"
    - "Show me the top 10 slow queries."
    - "Optimize this SQL."
    """
    try:
        return optimizer_agent.process_chat(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")
