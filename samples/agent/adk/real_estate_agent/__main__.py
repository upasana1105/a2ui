import logging
import os
import click
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2ui.a2ui_extension import get_a2ui_agent_extension
from agent_executor import RealEstateAgentExecutor
from agent import RealEstateAgent
from tools import IMAGE_CACHE
from genai_utils import generate_property_image
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response
import httpx

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=10003)
def main(host, port):
    try:
        capabilities = AgentCapabilities(
            streaming=True,
            extensions=[get_a2ui_agent_extension()],
        )
        skill = AgentSkill(
            id="find_properties",
            name="Property Finder",
            description="Finds houses, apartments, and listings based on user criteria.",
            tags=["realestate", "housing"],
            examples=["Find me houses in Palo Alto near a gym"],
        )

        base_url = f"http://{host}:{port}"
        agent_card = AgentCard(
            name="Real Estate Agent",
            description="Your expert assistant for finding properties.",
            url=base_url,
            version="1.0.0",
            default_input_modes=RealEstateAgent.SUPPORTED_CONTENT_TYPES,
            default_output_modes=RealEstateAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        agent_executor = RealEstateAgentExecutor(base_url=base_url)
        request_handler = DefaultRequestHandler(
            agent_executor=agent_executor,
            task_store=InMemoryTaskStore(),
        )
        server = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)
        app = server.build()

        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r"http://localhost:\d+",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.route("/proxy-image")
        async def proxy_image(request):
            place_id = request.query_params.get("id", "house")
            photo_ref = IMAGE_CACHE.get(place_id)
            api_key = os.getenv("GOOGLE_MAPS_API_KEY")
            
            # Seeded house-centric placeholder function
            def get_placeholder(seed):
                safe_seed = seed or "home"
                # Using LoremFlickr with a 'lock' to ensure uniqueness and relevance
                return f"https://loremflickr.com/800/600/house,interior,home/all?lock={hash(safe_seed) % 10000}"

            from starlette.responses import RedirectResponse

            if not photo_ref or not api_key:
                logger.warning(f"No photo_ref found for id {place_id} or missing api_key. Generating AI image.")
                desc = request.query_params.get("desc", "A beautiful residential house")
                ai_image_path = await generate_property_image(desc, place_id)
                if ai_image_path:
                    from starlette.responses import FileResponse
                    return FileResponse(ai_image_path)
                return RedirectResponse(url=get_placeholder(place_id))
            
            # Use params for safe encoding by httpx
            base_url = "https://maps.googleapis.com/maps/api/place/photo"
            params = {
                "maxwidth": 800,
                "photo_reference": photo_ref,
                "key": api_key
            }
            
            client = httpx.AsyncClient(follow_redirects=True)
            try:
                masked_key = f"{api_key[:5]}...{api_key[-5:]}" if api_key else "None"
                logger.debug(f"Proxying image request for ref: {photo_ref[:20]}... using key: {masked_key}")
                
                req = client.build_request("GET", base_url, params=params)
                r = await client.send(req, stream=True)
                
                if r.status_code != 200:
                    error_body = await r.aread()
                    logger.error(f"Upstream image fetch failed: {r.status_code} for ref: {photo_ref[:20]}. fallback to placeholder.")
                    await r.aclose()
                    await client.aclose()
                    desc = request.query_params.get("desc", "A beautiful residential house")
                    ai_image_path = await generate_property_image(desc, place_id)
                    if ai_image_path:
                        from starlette.responses import FileResponse
                        return FileResponse(ai_image_path)
                    return RedirectResponse(url=get_placeholder(place_id))

                async def stream_content():
                    try:
                        async for chunk in r.aiter_bytes():
                            yield chunk
                    finally:
                        await r.aclose()
                        await client.aclose()

                from starlette.responses import StreamingResponse
                return StreamingResponse(stream_content(), media_type=r.headers.get("Content-Type", "image/jpeg"))
            except Exception as e:
                logger.error(f"Exception in proxy_image: {e}")
                await client.aclose()
                desc = request.query_params.get("desc", "A beautiful residential house")
                ai_image_path = await generate_property_image(desc, place_id)
                if ai_image_path:
                    from starlette.responses import FileResponse
                    return FileResponse(ai_image_path)
                return RedirectResponse(url=get_placeholder(place_id))

        logger.info(f"Starting Real Estate Agent on {base_url}")
        uvicorn.run(app, host=host, port=port)
    except Exception as e:
        logger.error(f"Startup error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
