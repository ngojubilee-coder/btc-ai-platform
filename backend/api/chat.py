"""Chat API — SSE streaming chatbot endpoint with RAG + function calling."""
import json
import re
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from core.llm import llm_router
from core.rag import rag_engine
from core.tools import TOOLS, execute_tool
from core.agent import SYSTEM_PROMPT, get_system_prompt
from db.supabase_client import save_message, create_conversation, get_messages, get_conversations, delete_conversation

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    user_id: str = "anonymous"
    complexity: str = "simple"
    lang: str = "fr"


class CreateConversationRequest(BaseModel):
    title: str = "New conversation"
    asset: str = "BTC"
    user_id: str


@router.get("/conversations/{user_id}")
async def list_conversations(user_id: str):
    try:
        return await get_conversations(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/{conversation_id}")
async def list_messages(conversation_id: str):
    try:
        return await get_messages(conversation_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations")
async def new_conversation(body: CreateConversationRequest):
    try:
        return await create_conversation(body.user_id, body.title, body.asset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}")
async def del_conversation(conversation_id: str):
    try:
        await delete_conversation(conversation_id)
        return {"deleted": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(body: ChatRequest):
    """Stream chatbot response via Server-Sent Events."""

    async def event_generator():
        # 1. RAG retrieval
        rag_context = await rag_engine.retrieve_and_format(body.message)

        # 2. Auto-create conversation if none provided
        conversation_id = body.conversation_id
        if not conversation_id:
            try:
                conv = await create_conversation(body.user_id, title=body.message[:50] or ("New conversation" if body.lang == "en" else "Nouvelle conversation"))
                conversation_id = conv.get("id")
            except Exception:
                conversation_id = None

        # 3. Load conversation history
        history = []
        if conversation_id:
            msgs = await get_messages(conversation_id)
            history = [{"role": m["role"], "content": m["content"]} for m in msgs[-10:]]

        # 4. Build system prompt with RAG context
        L = body.lang == "en"
        system = get_system_prompt(body.lang)
        if rag_context:
            system += f"\n\n{('RELEVANT DOCUMENTS (RAG context):' if L else 'CONTEXTE RAG (documents pertinents):')}\n{rag_context}"

        # 5. Save user message
        if conversation_id:
            await save_message(conversation_id, "user", body.message)

        # 6. Build messages for LLM
        messages = history + [{"role": "user", "content": body.message}]

        # 6. Pre-execute relevant tools based on keyword detection
        tools_summary = []
        msg_lower = body.message.lower()
        tool_context = ""

        try:
            if any(kw in msg_lower for kw in ["statistique", "stats", "combien", "taille", "ligne", "nombre", "how many", "how much", "size", "rows", "count"]):
                result = await execute_tool("get_dataset_stats", {})
                tool_context += f"\n[{('DATASET STATISTICS' if L else 'STATISTIQUES DATASET')}]\n{result}\n"
                tools_summary.append("get_dataset_stats")

            if any(kw in msg_lower for kw in ["schema", "colonne", "colonnes", "structure", "quels colonnes", "columns", "what columns", "field"]):
                result = await execute_tool("get_dataset_schema", {})
                tool_context += f"\n[{('DATASET SCHEMA' if L else 'SCHEMA DATASET')}]\n{result}\n"
                tools_summary.append("get_dataset_schema")

            if any(kw in msg_lower for kw in ["correlation", "corrél", "influence", "importante", "feature la plus", "quelles features", "which features", "correlate", "correlation", "most important feature", "impact"]):
                result = await execute_tool("get_correlations", {"top_n": 20})
                tool_context += f"\n[{('TOP CORRELATIONS' if L else 'TOP CORRELATIONS')}]\n{result}\n"
                tools_summary.append("get_correlations")

            if any(kw in msg_lower for kw in ["actualit", "news", "événement", "evenement", "fed", "cpi", "etf", "halving", "hack", "pourquoi btc", "chute", "hausse", "crash", "event", "why btc", "drop", "rise", "pump", "dump"]):
                result = await execute_tool("search_news", {"limit": 10})
                tool_context += f"\n[{('RECENT NEWS' if L else 'ACTUALITÉS RÉCENTES')}]\n{result}\n"
                tools_summary.append("search_news")

            if any(kw in msg_lower for kw in ["échantillon", "sample", "exemple", "aperçu", "données", "example", "preview", "data sample", "show data"]):
                result = await execute_tool("sample_data", {"n": 50})
                tool_context += f"\n[{('DATA SAMPLE' if L else 'ÉCHANTILLON DONNÉES')}]\n{result}\n"
                tools_summary.append("sample_data")

            if any(kw in msg_lower for kw in ["whale", "baleine", "wallet", "porte-monnaie", "porte monnaie", "adresse btc", "exchange wallet", "cold wallet", "holder", "large holder"]):
                result = await execute_tool("get_whale_stats", {})
                tool_context += f"\n[{('WHALE STATS' if L else 'STATS WHALE')}]\n{result}\n"
                result2 = await execute_tool("get_top_whales", {"limit": 10})
                tool_context += f"\n[{('TOP WHALES' if L else 'TOP WHALES')}]\n{result2}\n"
                tools_summary.append("get_whale_stats")

                # If the message contains a BTC address or specific entity name, also search
                addr_match = re.search(r'(bc1[a-z0-9]{20,}|[13][a-km-zA-HJ-NP-Z1-9]{25,})', body.message)
                if addr_match:
                    result3 = await execute_tool("search_whales", {"query": addr_match.group(0), "limit": 5})
                    tool_context += f"\n[{('SEARCH WHALE BY ADDRESS' if L else 'SEARCH WHALE BY ADDRESS')}]\n{result3}\n"
                    tools_summary.append("search_whales")
                else:
                    # Check for known entity names
                    known_entities = ["binance", "coinbase", "bitfinex", "kraken", "okx", "bybit", "huobi", "mt gox", "mtgox", "grayscale", "microstrategy", "tesla", "block.one", "fidelity", "blackrock", "satoshi", "ultra"]
                    msg_lower_words = msg_lower
                    for entity in known_entities:
                        if entity in msg_lower_words:
                            result3 = await execute_tool("search_whales", {"query": entity, "limit": 5})
                            tool_context += f"\n[{('SEARCH WHALE BY ENTITY: ' + entity) if L else ('SEARCH WHALE BY ENTITY: ' + entity)}]\n{result3}\n"
                            tools_summary.append("search_whales")
                            break
        except Exception as e:
            tool_context += f"\n[{('TOOL ERROR' if L else 'ERREUR TOOL')}]\n{e}\n"

        if tool_context:
            system += f"\n\n{('REAL DATA (pre-executed via tools):' if L else 'DONNÉES RÉELLES (pré-exécutées via tools):')}\n{tool_context}"

        # 7. Stream LLM response
        full_response = ""

        # Add tool descriptions for awareness
        tool_descriptions = "\n".join([
            f"- {t['name']}: {t['description']}" for t in TOOLS
        ])
        system += f"\n\n{('AVAILABLE TOOLS (reference):' if L else 'OUTILS DISPONIBLES (référence):')}\n{tool_descriptions}"

        try:
            async for chunk in llm_router.stream(
                messages=messages,
                system_prompt=system,
                complexity=body.complexity,
                temperature=0.7,
                max_tokens=4096,
                tool_context=tool_context,
            ):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            full_response = f"Error: {e}"

        # 8. Save assistant message
        if conversation_id:
            await save_message(conversation_id, "assistant", full_response, llm_router._select_model(body.complexity), tools_summary)

        # 9. Send done event
        yield f"data: {json.dumps({'type': 'done', 'content': full_response, 'conversation_id': conversation_id})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/execute-tool")
async def execute_tool_endpoint(body: dict):
    """Execute a tool directly (for testing)."""
    name = body.get("name")
    arguments = body.get("arguments", {})
    if not name:
        raise HTTPException(status_code=400, detail="Tool name required")
    result = await execute_tool(name, arguments)
    return {"result": result}
