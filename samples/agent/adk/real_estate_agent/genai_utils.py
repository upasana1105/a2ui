import os
import logging
import base64
import hashlib
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# Ensure cache directory exists
CACHE_DIR = "/tmp/re_images"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_gemini_client():
    """Builds the GenAI client using environment variables."""
    # Prioritize GOOGLE_CLOUD_API_KEY as provided by the user for Gemini 3
    api_key = os.environ.get("GOOGLE_CLOUD_API_KEY") or os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        logger.error("No API key found for Gemini Image Generation.")
        return None
        
    return genai.Client(
        vertexai=False,
        api_key=api_key,
    )

async def generate_property_image(description: str, seed: str) -> str:
    """
    Generates a property image using Imagen 3 based on the description.
    Returns the path to the cached image.
    """
    # Create a unique filename based on the seed (e.g. place_id)
    safe_seed = hashlib.md5(seed.encode()).hexdigest()
    image_path = os.path.join(CACHE_DIR, f"{safe_seed}.png")
    
    # Check if already cached
    if os.path.exists(image_path):
        logger.info(f"Using cached AI image for {seed}")
        return image_path

    logger.info(f"Generating AI image for: {description}")
    client = get_gemini_client()
    if not client:
        return None

    model = "gemini-3-pro-image-preview"
    
    # Prompt enhancement for high-quality real estate images
    enhanced_desc = description if description and len(description) > 5 else "A beautiful residential house"
    prompt = f"A high-quality, professional real estate photograph of {enhanced_desc}. Sunny day, realistic, architectural photography style, wide angle."
    
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)]
        )
    ]

    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        max_output_tokens=32768,
        response_modalities=["IMAGE"], # We only want the image
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
        ],
        image_config=types.ImageConfig(
            aspect_ratio="1:1",
            image_size="1K",
            # output_mime_type is not supported in Gemini API (vertexai=False)
        ),
    )

    try:
        # We use non-streaming generation for simplicity when saving to file
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config,
        )
        
        # Extract the image from the parts
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                # Save the image
                with open(image_path, "wb") as f:
                    f.write(part.inline_data.data)
                logger.info(f"Successfully generated and cached AI image: {image_path}")
                return image_path
                
        logger.warning("No image data found in Gemini response candidate parts.")
    except Exception as e:
        logger.error(f"Error generating image with Gemini: {e}")
        
    return None
