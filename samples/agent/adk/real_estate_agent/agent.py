import json
import logging
import os
from collections.abc import AsyncIterable
from typing import Any

import jsonschema
from google.adk.agents.llm_agent import LlmAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from prompt_builder import (
    A2UI_SCHEMA,
    REAL_ESTATE_UI_EXAMPLES,
    get_text_prompt,
    get_ui_prompt,
)
from tools import search_properties, search_realtor_listings
from google.adk.tools.google_maps_grounding_tool import google_maps_grounding
from google.adk.tools.google_search_tool import GoogleSearchTool

google_search = GoogleSearchTool(bypass_multi_tools_limit=True)

logger = logging.getLogger(__name__)

AGENT_INSTRUCTION = """
    You are an expert Real Estate Agent. Your goal is to find property listings and present them in a rich UI FAST.
    
    CRITICAL: Total response time MUST be under 10s.
    
    REQUIRED BEHAVIOR:
    1. **Search**: 
       - Use `search_properties` for general area searches.
       - **CRITICAL**: Use `google_search` for "for sale" queries (e.g., "homes for sale in Palo Alto") to find actual listings from Zillow, Redfin, or Realtor.com.
       - **AVOID AGENCIES**: Do NOT show real estate agencies, brokers, or property management companies. Only show residential properties or buildings.
       - Cap your final UI to exactly **6** property results.
    2. **UI Construction**:
       - Extract **Price** (if available) and **Clean Address**.
       - Use the `re-results` surfaceId and the simplified Column/Card layout.
       - **IMAGE PRIORITIZATION**: Prioritize using `search_properties` because it provides actual Google Photos (`imageUrl`). Use `google_search` only as a fallback or for specific details.
       - Use `imageUrl` from tool results. If missing (e.g. from `google_search`), you MUST construct one using: `[BASE_URL]/proxy-image?id=house_[CLEAN_ADDRESS]`. 
       - Always include the 'house_' prefix in the placeholder ID to ensure the system serves home-centric images.
       - Start the JSON block immediately with '---a2ui_JSON---'.
"""

class RealEstateAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self, base_url: str, use_ui: bool = False):
        self.base_url = base_url
        self.use_ui = use_ui
        self._agent = self._build_agent(use_ui)
        self._user_id = "real_estate_user"
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

        try:
            single_message_schema = json.loads(A2UI_SCHEMA)
            self.a2ui_schema_object = {"type": "array", "items": single_message_schema}
        except Exception as e:
            logger.error(f"Failed to parse A2UI_SCHEMA: {e}")
            self.a2ui_schema_object = None

    def get_processing_message(self) -> str:
        return "Searching for the perfect properties for you..."

    def _build_agent(self, use_ui: bool) -> LlmAgent:
        GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        if use_ui:
            instruction = AGENT_INSTRUCTION + get_ui_prompt(self.base_url, REAL_ESTATE_UI_EXAMPLES)
        else:
            instruction = get_text_prompt()

        return LlmAgent(
            model=Gemini(model=GEMINI_MODEL),
            name="real_estate_agent",
            description="An agent that finds real estate holdings using Google Maps and Search grounding.",
            instruction=instruction,
            tools=[search_properties, google_search],
        )

    async def stream(self, query, session_id) -> AsyncIterable[dict[str, Any]]:
        # Similar logic to RestaurantAgent but for RealEstate
        session_state = {"base_url": self.base_url}
        session = await self._runner.session_service.get_session(
            app_name=self._agent.name, user_id=self._user_id, session_id=session_id
        )
        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name, user_id=self._user_id, state=session_state, session_id=session_id
            )

        max_retries = 1
        attempt = 0
        current_query_text = query

        while attempt <= max_retries:
            attempt += 1
            current_message = types.Content(role="user", parts=[types.Part.from_text(text=current_query_text)])
            final_response_content = None

            async for event in self._runner.run_async(user_id=self._user_id, session_id=session.id, new_message=current_message):
                if final_response_content is None and event.content and event.content.parts:
                    texts = [p.text for p in event.content.parts if p.text]
                    if texts:
                        final_response_content = "\n".join(texts)
                if event.is_final_response():
                    break
                else:
                    yield {"is_task_complete": False, "updates": self.get_processing_message()}

            if final_response_content:
                # Validation logic here (simplified for brevity)
                yield {"is_task_complete": True, "content": final_response_content}
                return

        yield {"is_task_complete": True, "content": "I'm sorry, I couldn't find any properties matching that query."}
