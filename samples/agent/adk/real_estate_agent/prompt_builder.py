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
Example 1: Premium Redfin-style Property List
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
        { "id": "cc", "component": { "Column": { "children": { "explicitList": ["img", "info_pad"] } } } },
        { "id": "img", "component": { "Image": { "url": { "path": "imageUrl" }, "usageHint": "mediumFeature", "fit": "cover" } } },
        { "id": "info_pad", "component": { "Column": { "children": { "explicitList": ["price_row", "details_row", "a", "feat_row"] } } } },
        {
          "id": "price_row",
          "component": { "Row": { "distribution": "spaceBetween", "alignment": "center", "children": { "explicitList": ["p", "act_row"] } } }
        },
        { "id": "p", "component": { "Text": { "text": { "path": "price" }, "usageHint": "h3" } } },
        { "id": "act_row", "component": { "Row": { "children": { "explicitList": ["sh", "fav", "vw_btn"] } } } },
        { "id": "sh", "component": { "Icon": { "name": { "literalString": "share" } } } },
        { "id": "fav", "component": { "Icon": { "name": { "literalString": "favorite" } } } },
        {
          "id": "vw_btn",
          "component": {
            "Button": {
              "child": "bt",
              "action": { "name": "OPEN_URL", "context": [{ "key": "url", "value": { "path": "publicUrl" } }] }
            }
          }
        },
        { "id": "bt", "component": { "Text": { "text": { "literalString": "VIEW" } } } },
        { "id": "details_row", "component": { "Row": { "children": { "explicitList": ["bd", "ba", "sq"] } } } },
        { "id": "bd", "component": { "Text": { "text": { "path": "beds" }, "usageHint": "body" } } },
        { "id": "ba", "component": { "Text": { "text": { "path": "baths" }, "usageHint": "body" } } },
        { "id": "sq", "component": { "Text": { "text": { "path": "sqft" }, "usageHint": "body" } } },
        { "id": "a", "component": { "Text": { "text": { "path": "address" }, "usageHint": "body" } } },
        { "id": "feat_row", "component": { "Text": { "text": { "path": "features" }, "usageHint": "caption" } } }
      ]
    }
  },
  {
    "dataModelUpdate": {
      "surfaceId": "re-results", "path": "/",
      "contents": [
        { "key": "title", "valueString": "3 Bedroom Homes in Palo Alto" },
        { 
          "key": "properties", 
          "valueMap": [
            {
              "key": "p1",
              "valueMap": [
                { "key": "price", "valueString": "$4,990,000" },
                { "key": "beds", "valueString": "4 beds" },
                { "key": "baths", "valueString": "4 baths" },
                { "key": "sqft", "valueString": "2,467 sq ft" },
                { "key": "address", "valueString": "852 La Para Ave, Palo Alto, CA 94306" },
                { "key": "features", "valueString": "Smart-home system • Tesla power wall • Private backyard" },
                { "key": "publicUrl", "valueString": "https://..." },
                { "key": "imageUrl", "valueString": "http://localhost:10003/proxy-image?id=house_852_la_para" }
              ]
            }
          ]
        }
      ]
    }
  }
]
'''

def get_ui_prompt(base_url: str, examples: str) -> str:
    # Use regular string concatenation to avoid braces issue
    return """
    The following is the A2UI JSON schema that you MUST use for all UI responses:
    """ + A2UI_SCHEMA + """

    When generating the UI, you MUST follow these rules:
    1. Only use component types and properties defined in the schema.
    2. Ensure every component has a unique ID.
    3. The response MUST be a valid JSON array of A2UI messages.
    4. Start the JSON block with the delimiter '---a2ui_JSON---'.
    5. DATA INTEGRITY: Use paths for all dynamic property data (price, beds, baths, sqft, features, imageUrl, publicUrl).
    6. NO EMPTY LABELS: If a field is missing, omit it from the dataModelUpdate. Do NOT use "(empty)".
    
    Here are some examples of valid A2UI JSON:
    """ + examples

def get_text_prompt() -> str:
    return "You are a real estate agent. Help the user find properties and provide information about them."
