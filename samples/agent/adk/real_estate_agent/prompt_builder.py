import json

A2UI_SCHEMA = r'''
{
  "title": "A2UI Message Schema",
  "type": "object",
  "properties": {
    "beginRendering": { "type": "object", "required": ["root", "surfaceId"] },
    "surfaceUpdate": { "type": "object", "required": ["surfaceId", "components"] },
    "dataModelUpdate": { "type": "object", "required": ["contents", "surfaceId"] }
  }
}
'''

REAL_ESTATE_UI_EXAMPLES = r'''
Example 1: List of property cards
---a2ui_JSON---
[
  { "beginRendering": { "surfaceId": "re-results", "root": "root" } },
  {
    "surfaceUpdate": {
      "surfaceId": "re-results",
      "components": [
        { "id": "root", "component": { "Column": { "children": { "explicitList": ["h1", "plist"] } } } },
        { "id": "h1", "component": { "Text": { "text": { "path": "/title" }, "usageHint": "h2" } } },
        {
          "id": "plist",
          "component": { "List": { "children": { "template": { "componentId": "c", "dataBinding": "/properties" } } } }
        },
        { "id": "c", "component": { "Card": { "child": "cc" } } },
        { "id": "cc", "component": { "Column": { "children": { "explicitList": ["img", "n", "a", "f"] } } } },
        { "id": "img", "component": { "Image": { "url": { "path": "imageUrl" }, "usageHint": "mediumFeature", "fit": "cover" } } },
        { "id": "n", "component": { "Text": { "text": { "path": "name" }, "usageHint": "h3" } } },
        { "id": "a", "component": { "Text": { "text": { "path": "address" }, "usageHint": "body" } } },
        {
          "id": "f",
          "component": { "Row": { "distribution": "spaceBetween", "alignment": "center", "children": { "explicitList": ["r", "b"] } } }
        },
        { "id": "r", "component": { "Text": { "text": { "path": "rating" }, "usageHint": "caption" } } },
        {
          "id": "b",
          "component": {
            "Button": {
              "child": "bt", "primary": true,
              "action": { "name": "OPEN_URL", "context": [{ "key": "url", "value": { "path": "publicUrl" } }] }
            }
          }
        },
        { "id": "bt", "component": { "Text": { "text": { "literalString": "View" } } } }
      ]
    }
  },
  {
    "dataModelUpdate": {
      "surfaceId": "re-results", "path": "/",
      "contents": [
        { "key": "title", "valueString": "Homes in Palo Alto" },
        { 
          "key": "properties", 
          "valueMap": [
            {
              "key": "p1",
              "valueMap": [
                { "key": "name", "valueString": "$1.5M Listing" },
                { "key": "address", "valueString": "123 Main St" },
                { "key": "rating", "valueString": "4.5 Stars" },
                { "key": "publicUrl", "valueString": "https://..." },
                { "key": "imageUrl", "valueString": "http://localhost:10003/proxy-image?id=p1" }
              ]
            }
          ]
        }
      ]
    }
  }
]

Example 2: No properties found
---a2ui_JSON---
[
  { "beginRendering": { "surfaceId": "re-results", "root": "root" } },
  {
    "surfaceUpdate": {
      "surfaceId": "re-results",
      "components": [
        { "id": "root", "component": { "Column": { "children": { "explicitList": ["h1", "t"] } } } },
        { "id": "h1", "component": { "Text": { "text": { "path": "/title" }, "usageHint": "h2" } } },
        { "id": "t", "component": { "Text": { "text": { "path": "/msg" }, "usageHint": "body" } } }
      ]
    }
  },
  {
    "dataModelUpdate": {
      "surfaceId": "re-results", "path": "/",
      "contents": [
        { "key": "title", "valueString": "No Results" },
        { "key": "msg", "valueString": "Try a broader search." }
      ]
    }
  }
]
'''

def get_ui_prompt(base_url: str, examples: str) -> str:
    return f"""
    The following is the A2UI JSON schema that you MUST use for all UI responses:
    {A2UI_SCHEMA}

    When generating the UI, you MUST follow these rules:
    1. Only use component types and properties defined in the schema.
    2. Ensure every component has a unique ID.
    3. The response MUST be a valid JSON array of A2UI messages.
    4. Start the JSON block with the delimiter '---a2ui_JSON---'.
    
    Here are some examples of valid A2UI JSON:
    {examples}
    """

def get_text_prompt() -> str:
    return "You are a real estate agent. Help the user find properties and provide information about them."
