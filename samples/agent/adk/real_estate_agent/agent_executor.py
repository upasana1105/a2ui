import json
import logging
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    DataPart,
    Part,
    Task,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import (
    new_agent_parts_message,
    new_agent_text_message,
    new_task,
)
from a2a.utils.errors import ServerError
from a2ui.a2ui_extension import create_a2ui_part, try_activate_a2ui_extension
from agent import RealEstateAgent

logger = logging.getLogger(__name__)

class RealEstateAgentExecutor(AgentExecutor):
    def __init__(self, base_url: str):
        self.ui_agent = RealEstateAgent(base_url=base_url, use_ui=True)
        self.text_agent = RealEstateAgent(base_url=base_url, use_ui=False)

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        use_ui = try_activate_a2ui_extension(context)
        agent = self.ui_agent if use_ui else self.text_agent
        query = context.get_user_input()

        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        async for item in agent.stream(query, task.context_id):
            if not item["is_task_complete"]:
                await updater.update_status(
                    TaskState.working,
                    new_agent_text_message(item["updates"], task.context_id, task.id),
                )
                continue

            content = item["content"]
            logger.info(f"Final LLM content: {content[:1000]}...")
            final_parts = []
            if "---a2ui_JSON---" in content:
                text_content, json_string = content.split("---a2ui_JSON---", 1)
                if text_content.strip():
                    final_parts.append(Part(root=TextPart(text=text_content.strip())))
                
                try:
                    json_string_cleaned = json_string.strip()
                    # Find the first '[' or '{' and the last ']' or '}'
                    first_item = min([json_string_cleaned.find(c) for c in '[{' if json_string_cleaned.find(c) != -1] or [0])
                    last_item = max([json_string_cleaned.rfind(c) for c in ']}' if json_string_cleaned.rfind(c) != -1] or [len(json_string_cleaned)])
                    json_string_cleaned = json_string_cleaned[first_item:last_item+1]
                    
                    try:
                        json_data = json.loads(json_string_cleaned)
                        if isinstance(json_data, list):
                            for message in json_data:
                                final_parts.append(create_a2ui_part(message))
                        else:
                            final_parts.append(create_a2ui_part(json_data))
                    except json.JSONDecodeError:
                        # Fallback: simple split if it looks like multiple objects
                        # The recursive regex was broken, let's just try to find objects by braces
                        # if they are top-level. 
                        logger.warning("JSONDecodeError, attempting fallback splitting")
                        # This is still a bit of a guess, but better than a crash
                        potential_objects = []
                        if json_string_cleaned.startswith('[') and json_string_cleaned.endswith(']'):
                            # It's a list but maybe has issues inside? 
                            # If it's a list, the previous json.loads should have worked unless truncated.
                            pass
                        
                        # If we can't parse it as one, and it's not a crash-inducing regex, 
                        # let's just log the error and move on if we can't easily fix it.
                        raise # Re-raise to be caught by the outer try-except for logging
                except Exception as e:
                    logger.error(f"Failed to parse UI JSON: {e}")
                    final_parts.append(Part(root=TextPart(text=json_string)))
            else:
                final_parts.append(Part(root=TextPart(text=content.strip())))

            await updater.update_status(
                TaskState.input_required,
                new_agent_parts_message(final_parts, task.context_id, task.id),
            )
            break

    async def cancel(self, request: RequestContext, event_queue: EventQueue) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())
