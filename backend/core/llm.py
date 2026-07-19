"""LLM Router — route requests between Gemini, Claude, and Ollama based on complexity."""
import json
from typing import AsyncIterator
from core.config import settings
from core.logging_config import logger

_PLACEHOLDERS = {"your-gemini-key", "your-openai-key", "your-anthropic-key", "your-api-key", "placeholder", ""}


def _has_valid_key(key: str) -> bool:
    return bool(key) and key not in _PLACEHOLDERS


class LLMRouter:
    """Routes LLM requests based on complexity and availability."""

    def __init__(self):
        self._gemini = None
        self._claude = None
        self._openai = None

    @property
    def gemini(self):
        if self._gemini is None and _has_valid_key(settings.gemini_api_key):
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            self._gemini = genai.GenerativeModel(getattr(settings, "gemini_model", "gemini-2.0-flash"))
        return self._gemini

    @property
    def claude(self):
        if self._claude is None and _has_valid_key(settings.anthropic_api_key):
            import anthropic
            self._claude = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        return self._claude

    @property
    def openai(self):
        if self._openai is None and _has_valid_key(settings.openai_api_key):
            from openai import AsyncOpenAI
            self._openai = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._openai

    def _select_model(self, complexity: str = "simple") -> str:
        if complexity == "complex":
            if _has_valid_key(settings.anthropic_api_key):
                return "claude"
            if _has_valid_key(settings.gemini_api_key):
                return "gemini"
        if _has_valid_key(settings.gemini_api_key):
            return "gemini"
        if _has_valid_key(settings.openai_api_key):
            return "openai"
        if _has_valid_key(settings.anthropic_api_key):
            return "claude"
        return "ollama"

    def _get_fallback_chain(self, complexity: str = "simple") -> list[str]:
        """Return ordered list of models to try based on availability."""
        primary = self._select_model(complexity)
        chain = [primary]
        for m in ["gemini", "claude", "openai", "ollama"]:
            if m != primary and m != "ollama":
                if m == "gemini" and _has_valid_key(settings.gemini_api_key):
                    chain.append(m)
                elif m == "claude" and _has_valid_key(settings.anthropic_api_key):
                    chain.append(m)
                elif m == "openai" and _has_valid_key(settings.openai_api_key):
                    chain.append(m)
            elif m == "ollama" and m != primary:
                chain.append(m)
        chain.append("local")
        return chain

    async def generate(
        self,
        messages: list[dict],
        system_prompt: str = "",
        complexity: str = "simple",
        tools: list[dict] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict:
        chain = self._get_fallback_chain(complexity)
        last_error = None
        for model in chain:
            try:
                if model == "gemini":
                    return await self._call_gemini(messages, system_prompt, tools, temperature, max_tokens)
                elif model == "claude":
                    return await self._call_claude(messages, system_prompt, tools, temperature, max_tokens)
                elif model == "openai":
                    return await self._call_openai(messages, system_prompt, tools, temperature, max_tokens)
                elif model == "local":
                    return await self._call_local(messages, system_prompt)
                else:
                    return await self._call_ollama(messages, system_prompt, temperature, max_tokens)
            except Exception as e:
                logger.warning(f"[LLM] {model} failed: {e}, trying fallback...")
                last_error = e
        raise Exception(f"All LLM providers failed. Last error: {last_error}")

    async def stream(
        self,
        messages: list[dict],
        system_prompt: str = "",
        complexity: str = "simple",
        tools: list[dict] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        chain = self._get_fallback_chain(complexity)
        last_error = None
        for model in chain:
            try:
                if model == "gemini":
                    async for chunk in self._stream_gemini(messages, system_prompt, tools, temperature, max_tokens):
                        yield chunk
                    return
                elif model == "claude":
                    async for chunk in self._stream_claude(messages, system_prompt, tools, temperature, max_tokens):
                        yield chunk
                    return
                elif model == "openai":
                    async for chunk in self._stream_openai(messages, system_prompt, tools, temperature, max_tokens):
                        yield chunk
                    return
                elif model == "local":
                    async for chunk in self._stream_local(messages, system_prompt):
                        yield chunk
                    return
                else:
                    async for chunk in self._stream_ollama(messages, system_prompt, temperature, max_tokens):
                        yield chunk
                    return
            except Exception as e:
                logger.warning(f"[LLM Stream] {model} failed: {e}, trying fallback...")
                last_error = e
        yield f"[Error] All LLM providers failed. Last error: {last_error}"

    @staticmethod
    def _map_gemini_role(role: str) -> str:
        """Map standard chat roles to Gemini-compatible roles."""
        return "model" if role == "assistant" else role

    async def _call_gemini(self, messages, system_prompt, tools, temperature, max_tokens) -> dict:
        full_messages = messages
        if system_prompt:
            full_messages = [{"role": "user", "content": system_prompt}, {"role": "model", "content": "Understood."}] + messages
        history = [{"role": self._map_gemini_role(m["role"]), "parts": [m["content"]]} for m in full_messages[:-1]]
        chat = self.gemini.start_chat(history=history)
        resp = await chat.send_message_async(
            full_messages[-1]["content"],
            generation_config={"temperature": temperature, "max_output_tokens": max_tokens},
        )
        return {"model": "gemini", "content": resp.text, "tool_calls": []}

    async def _stream_gemini(self, messages, system_prompt, tools, temperature, max_tokens) -> AsyncIterator[str]:
        full_messages = messages
        if system_prompt:
            full_messages = [{"role": "user", "content": system_prompt}, {"role": "model", "content": "Understood."}] + messages
        history = [{"role": self._map_gemini_role(m["role"]), "parts": [m["content"]]} for m in full_messages[:-1]]
        chat = self.gemini.start_chat(history=history)
        resp = await chat.send_message_async(
            full_messages[-1]["content"],
            generation_config={"temperature": temperature, "max_output_tokens": max_tokens},
            stream=True,
        )
        async for chunk in resp:
            try:
                if chunk.text:
                    yield chunk.text
            except (ValueError, AttributeError):
                continue

    async def _call_claude(self, messages, system_prompt, tools, temperature, max_tokens) -> dict:
        resp = await self.claude.messages.create(
            model="claude-3-5-sonnet-20241022",
            system=system_prompt,
            messages=[{"role": m["role"], "content": m["content"]} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return {"model": "claude", "content": resp.content[0].text, "tool_calls": []}

    async def _stream_claude(self, messages, system_prompt, tools, temperature, max_tokens) -> AsyncIterator[str]:
        async with self.claude.messages.stream(
            model="claude-3-5-sonnet-20241022",
            system=system_prompt,
            messages=[{"role": m["role"], "content": m["content"]} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def _call_openai(self, messages, system_prompt, tools, temperature, max_tokens) -> dict:
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)
        resp = await self.openai.chat.completions.create(
            model="gpt-4o",
            messages=msgs,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return {"model": "openai", "content": resp.choices[0].message.content, "tool_calls": []}

    async def _stream_openai(self, messages, system_prompt, tools, temperature, max_tokens) -> AsyncIterator[str]:
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)
        stream = await self.openai.chat.completions.create(
            model="gpt-4o",
            messages=msgs,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def _call_ollama(self, messages, system_prompt, temperature, max_tokens) -> dict:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/chat",
                json={
                    "model": "llama3.3:70b",
                    "messages": [{"role": "system", "content": system_prompt}] + messages if system_prompt else messages,
                    "stream": False,
                    "options": {"temperature": temperature, "num_predict": max_tokens},
                },
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            return {"model": "ollama", "content": data.get("message", {}).get("content", ""), "tool_calls": []}

    async def _stream_ollama(self, messages, system_prompt, temperature, max_tokens) -> AsyncIterator[str]:
        import httpx
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{settings.ollama_base_url}/api/chat",
                json={
                    "model": "llama3.3:70b",
                    "messages": [{"role": "system", "content": system_prompt}] + messages if system_prompt else messages,
                    "stream": True,
                    "options": {"temperature": temperature, "num_predict": max_tokens},
                },
                timeout=120,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if data.get("message", {}).get("content"):
                            yield data["message"]["content"]

    async def _call_local(self, messages: list[dict], system_prompt: str = "") -> dict:
        """Local fallback — generates a helpful response without external LLM."""
        user_msg = messages[-1].get("content", "") if messages else ""
        response = self._generate_local_response(user_msg, system_prompt)
        return {"model": "local", "content": response, "tool_calls": []}

    async def _stream_local(self, messages: list[dict], system_prompt: str = "") -> AsyncIterator[str]:
        """Stream local fallback response token by token."""
        user_msg = messages[-1].get("content", "") if messages else ""
        response = self._generate_local_response(user_msg, system_prompt)
        words = response.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            import asyncio
            await asyncio.sleep(0.02)

    @staticmethod
    def _generate_local_response(user_msg: str, system_prompt: str = "") -> str:
        """Generate a context-aware local response without external LLM."""
        msg_lower = user_msg.lower()

        if any(kw in msg_lower for kw in ["bonjour", "hello", "salut", "hi", "hey"]):
            return ("Bonjour ! Je suis l'analyste quantitatif BTC AI Platform. "
                    "Je peux analyser le dataset Bitcoin (100 000 lignes), les corrélations, "
                    "les whales (211 wallets), et les actualités crypto. "
                    "Note: Le LLM externe n'est pas configuré — mode local actif. "
                    "Posez-moi une question sur le dataset, les whales, ou les corrélations !")

        if any(kw in msg_lower for kw in ["dataset", "data", "données", "lignes", "colonnes"]):
            return ("📊 **Dataset BTC**\n\n"
                    "- **Lignes**: 100 000\n"
                    "- **Colonnes**: 31 (prix, indicateurs techniques, targets)\n"
                    "- **Période**: 2023-01-01 à 2023-03-11\n"
                    "- **Format**: Parquet (29.6 MB)\n"
                    "- **Indicateurs**: SMA, EMA, RSI, MACD, Bollinger Bands, volatilité\n\n"
                    "Utilisez le Data Explorer pour explorer les données en détail.")

        if any(kw in msg_lower for kw in ["whale", "baleine", "wallet"]):
            return ("🐋 **Whale Tracking**\n\n"
                    "- **Total wallets**: 211\n"
                    "- **Catégories**: Exchange, Mining, Fund, Individual, Unknown\n"
                    "- **Source**: whale_wallets_list.csv\n\n"
                    "Visitez la page Whales pour voir le classement complet.")

        if any(kw in msg_lower for kw in ["correlation", "corrélation", "feature"]):
            return ("📈 **Corrélations**\n\n"
                    "Les corrélations entre features et target_return_15m sont disponibles "
                    "dans la page Correlations. Les features les plus corrélées incluent "
                    "généralement RSI, MACD, et les bandes de Bollinger.")

        if any(kw in msg_lower for kw in ["model", "modèle", "training", "entraînement"]):
            return ("🤖 **Modèles ML**\n\n"
                    "Le système supporte XGBoost, RandomForest, et LSTM. "
                    "Visitez la page Training pour lancer un entraînement, "
                    "ou la page Models pour comparer les modèles existants.")

        if any(kw in msg_lower for kw in ["news", "actualité", "article"]):
            return ("📰 **Actualités Crypto**\n\n"
                    "Le système agrège des actualités de CoinDesk, Cointelegraph, "
                    "Bitcoin Magazine, The Block, et Federal Reserve. "
                    "Visitez la page News pour voir les dernières actualités.")

        return (f"J'ai reçu votre message: \"{user_msg[:200]}\"\n\n"
                "⚠️ **Mode local actif** — Aucun LLM externe n'est configuré (Gemini, Claude, OpenAI, Ollama).\n\n"
                "Je peux vous aider avec:\n"
                "- 📊 Analyse du dataset (100K lignes BTC)\n"
                "- 🐋 Whale tracking (211 wallets)\n"
                "- 📈 Corrélations et indicateurs techniques\n"
                "- 🤖 Modèles ML (XGBoost, RandomForest, LSTM)\n"
                "- 📰 Actualités crypto\n\n"
                "Configurez une clé API valide (GEMINI_API_KEY, ANTHROPIC_API_KEY, ou OPENAI_API_KEY) "
                "pour activer le LLM complet.")


llm_router = LLMRouter()
