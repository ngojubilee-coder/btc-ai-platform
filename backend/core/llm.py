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
        tool_context: str = "",
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
                    async for chunk in self._stream_local(messages, system_prompt, tool_context):
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

    async def _call_local(self, messages: list[dict], system_prompt: str = "", tool_context: str = "") -> dict:
        """Local fallback — generates a helpful response without external LLM."""
        user_msg = messages[-1].get("content", "") if messages else ""
        response = self._generate_local_response(user_msg, system_prompt, tool_context)
        return {"model": "local", "content": response, "tool_calls": []}

    async def _stream_local(self, messages: list[dict], system_prompt: str = "", tool_context: str = "") -> AsyncIterator[str]:
        """Stream local fallback response token by token."""
        user_msg = messages[-1].get("content", "") if messages else ""
        response = self._generate_local_response(user_msg, system_prompt, tool_context)
        words = response.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            import asyncio
            await asyncio.sleep(0.02)

    @staticmethod
    def _generate_local_response(user_msg: str, system_prompt: str = "", tool_context: str = "") -> str:
        """Generate a context-aware local response using real tool data when available."""
        msg_lower = user_msg.lower()
        L = "EN" in system_prompt[:200] and "FR" not in system_prompt[:200]

        # If we have real tool data, use it to build a rich response
        if tool_context:
            return LLMRouter._format_tool_response(user_msg, tool_context, L)

        if any(kw in msg_lower for kw in ["bonjour", "hello", "salut", "hi", "hey"]):
            return ("Bonjour ! Je suis l'analyste quantitatif BTC AI Platform. "
                    "Je peux analyser le dataset Bitcoin (100 000 lignes), les corrélations, "
                    "les whales (211 wallets), et les actualités crypto. "
                    "Note: Le LLM externe n'est pas configuré — mode local actif. "
                    "Posez-moi une question sur le dataset, les whales, ou les corrélations !")

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

    @staticmethod
    def _format_tool_response(user_msg: str, tool_context: str, is_en: bool) -> str:
        """Format a rich response using real tool data from tool_context."""
        import json as _json
        import re as _re
        L = is_en
        parts = []

        # Extract tool sections from tool_context
        # Sections look like: [DATASET STATISTICS]\n{json}\n
        sections = _re.findall(r'\[([^\]]+)\]\n(.*?)(?=\n\[|\Z)', tool_context, _re.DOTALL)

        for section_name, section_data in sections:
            section_name = section_name.strip()
            try:
                data = _json.loads(section_data.strip())
            except Exception:
                # Not JSON, include as-is
                parts.append(f"**{section_name}**\n```\n{section_data.strip()[:500]}\n```")
                continue

            if "DATASET STATISTICS" in section_name.upper() or "STATISTIQUES" in section_name.upper():
                parts.append(LLMRouter._format_dataset_stats(data, L))

            elif "SCHEMA" in section_name.upper():
                parts.append(LLMRouter._format_schema(data, L))

            elif "CORRELATION" in section_name.upper():
                parts.append(LLMRouter._format_correlations(data, L))

            elif "WHALE" in section_name.upper() and "STATS" in section_name.upper():
                parts.append(LLMRouter._format_whale_stats(data, L))

            elif "WHALE" in section_name.upper() and "TOP" in section_name.upper():
                parts.append(LLMRouter._format_top_whales(data, L))

            elif "WHALE" in section_name.upper() and "SEARCH" in section_name.upper():
                parts.append(LLMRouter._format_whale_search(data, L))

            elif "NEWS" in section_name.upper() or "ACTUALIT" in section_name.upper():
                parts.append(LLMRouter._format_news(data, L))

            elif "SAMPLE" in section_name.upper() or "ÉCHANTILLON" in section_name.upper():
                parts.append(LLMRouter._format_sample(data, L))

            else:
                # Generic formatting
                parts.append(f"**{section_name}**\n```\n{_json.dumps(data, indent=2, ensure_ascii=False)[:800]}\n```")

        if not parts:
            return (f"J'ai reçu votre message: \"{user_msg[:200]}\"\n\n"
                    "⚠️ **Mode local actif** — Aucun LLM externe n'est configuré.\n\n"
                    "Posez-moi une question sur le dataset, les whales, les corrélations, ou les actualités !")

        header = f"📊 **Analyse** — {user_msg[:100]}\n\n" if not L else f"� **Analysis** — {user_msg[:100]}\n\n"
        footer = ("\n\n---\n\n⚠️ *Mode local actif — configurez une clé API (GEMINI_API_KEY, ANTHROPIC_API_KEY, ou OPENAI_API_KEY) pour des analyses plus approfondies.*"
                  if not L else
                  "\n\n---\n\n⚠️ *Local mode active — configure an API key (GEMINI_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY) for deeper analysis.*")
        return header + "\n\n".join(parts) + footer

    @staticmethod
    def _format_dataset_stats(data: dict, L: bool) -> str:
        """Format dataset statistics as Markdown table."""
        rows = data.get("n_rows", 0)
        cols = data.get("n_columns", 0)
        size = data.get("file_size_mb", 0)
        min_d = data.get("min_timestamp", "N/A")
        max_d = data.get("max_timestamp", "N/A")
        title = "Dataset Statistics" if L else "Statistiques du Dataset"
        return (f"### {title}\n\n"
                f"| {'Metric' if L else 'Métrique'} | {'Value' if L else 'Valeur'} |\n"
                f"|----------|--------|\n"
                f"| {'Total rows' if L else 'Lignes totales'} | {rows:,} |\n"
                f"| {'Columns' if L else 'Colonnes'} | {cols} |\n"
                f"| {'File size' if L else 'Taille fichier'} | {size} MB |\n"
                f"| {'Min date' if L else 'Date min'} | {min_d} |\n"
                f"| {'Max date' if L else 'Date max'} | {max_d} |")

    @staticmethod
    def _format_schema(data: dict, L: bool) -> str:
        """Format schema as Markdown table."""
        columns = data.get("columns", [])
        title = "Dataset Schema" if L else "Schema du Dataset"
        lines = [f"### {title}\n\n| {'Column' if L else 'Colonne'} | Type |\n|--------|------|"]
        for c in columns[:30]:
            lines.append(f"| {c.get('name', '?')} | {c.get('type', '?')} |")
        if len(columns) > 30:
            lines.append(f"| ... | *{len(columns) - 30} {'more columns' if L else 'colonnes de plus'}* |")
        return "\n".join(lines)

    @staticmethod
    def _format_correlations(data: list, L: bool) -> str:
        """Format correlations as Markdown table."""
        if not data:
            return f"### {'Top Correlations' if L else 'Top Corrélations'}\n\n*{'No data' if L else 'Pas de données'}*"
        title = "Top Correlations (target_return_15m)" if L else "Top Corrélations (target_return_15m)"
        lines = [f"### {title}\n\n| Feature | {'Correlation' if L else 'Corrélation'} |\n|---------|------------|"]
        for c in data[:15]:
            feat = c.get("feature", "?")
            corr = c.get("correlation", 0)
            lines.append(f"| {feat} | {corr:+.4f} |")
        return "\n".join(lines)

    @staticmethod
    def _format_whale_stats(data: dict, L: bool) -> str:
        """Format whale stats as Markdown."""
        title = "Whale Statistics" if L else "Statistiques Whale"
        total = data.get("total_wallets", 0)
        total_btc = data.get("total_btc", 0)
        cats = data.get("categories", {})
        cat_lines = "\n".join(f"- **{k}**: {v}" for k, v in sorted(cats.items(), key=lambda x: -x[1]))
        return (f"### {title}\n\n"
                f"| {'Metric' if L else 'Métrique'} | {'Value' if L else 'Valeur'} |\n"
                f"|----------|--------|\n"
                f"| {'Total wallets' if L else 'Total wallets'} | {total} |\n"
                f"| {'Total BTC' if L else 'Total BTC'} | {total_btc:,.2f} |\n\n"
                f"**{'Categories' if L else 'Catégories'}:**\n{cat_lines}")

    @staticmethod
    def _format_top_whales(data: list, L: bool) -> str:
        """Format top whales as Markdown table."""
        if not data:
            return f"### {'Top Whales' if L else 'Top Whales'}\n\n*{'No data' if L else 'Pas de données'}*"
        title = "Top Whales by BTC Holdings" if L else "Top Whales par BTC"
        lines = [f"### {title}\n\n| # | {'Name' if L else 'Nom'} | Entity | BTC | {'Category' if L else 'Catégorie'} |\n|---|------|--------|-----|------------|"]
        for i, w in enumerate(data[:10], 1):
            name = w.get("name", "Unknown")[:20]
            entity = w.get("entity", "Unknown")[:15]
            btc = w.get("estimated_btc", 0) or 0
            cat = w.get("category", "?")
            lines.append(f"| {i} | {name} | {entity} | {btc:,.2f} | {cat} |")
        return "\n".join(lines)

    @staticmethod
    def _format_whale_search(data: list, L: bool) -> str:
        """Format whale search results."""
        if not data:
            return f"### {'Whale Search' if L else 'Recherche Whale'}\n\n*{'No results' if L else 'Aucun résultat'}*"
        title = "Whale Search Results" if L else "Résultats Recherche Whale"
        lines = [f"### {title}\n\n| {'Name' if L else 'Nom'} | Entity | BTC | Address |\n|------|--------|-----|---------|"]
        for w in data[:5]:
            name = w.get("name", "Unknown")[:20]
            entity = w.get("entity", "Unknown")[:15]
            btc = w.get("estimated_btc", 0) or 0
            addr = w.get("address", "")[:20]
            lines.append(f"| {name} | {entity} | {btc:,.2f} | {addr}... |")
        return "\n".join(lines)

    @staticmethod
    def _format_news(data: list, L: bool) -> str:
        """Format news articles as Markdown list."""
        if not data:
            return f"### {'Recent News' if L else 'Actualités Récentes'}\n\n*{'No news found' if L else 'Aucune actualité trouvée'}*"
        title = "Recent News" if L else "Actualités Récentes"
        lines = [f"### {title}\n"]
        for n in data[:8]:
            n_title = n.get("title", "Unknown")[:80]
            source = n.get("source", "?")
            etype = n.get("event_type", "market")
            date = n.get("event_date", "")[:10]
            lines.append(f"- **[{etype.upper()}]** {n_title} — *{source}* ({date})")
        return "\n".join(lines)

    @staticmethod
    def _format_sample(data: list, L: bool) -> str:
        """Format data sample as Markdown."""
        if not data:
            return f"### {'Data Sample' if L else 'Échantillon'}\n\n*{'No data' if L else 'Pas de données'}*"
        title = "Data Sample (first 5 rows)" if L else "Échantillon (5 premières lignes)"
        cols = list(data[0].keys())[:8]
        lines = [f"### {title}\n\n| {' | '.join(cols)} |", f"| {' | '.join(['---'] * len(cols))} |"]
        for row in data[:5]:
            vals = [str(row.get(c, ""))[:20] for c in cols]
            lines.append(f"| {' | '.join(vals)} |")
        return "\n".join(lines)


llm_router = LLMRouter()
