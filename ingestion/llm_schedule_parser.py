import litellm
import sys
import os
import json
import base64
from dotenv import load_dotenv

load_dotenv()
os.environ["GEMINI_API_KEY"] = os.getenv("INGESTION_API_KEY")

PROMPT = """You are a JSON extraction engine. You receive a campus safety shuttle schedule. Return ONLY a single valid JSON object — no markdown fences, no commentary, no preamble, no explanation. Raw JSON only.

The output MUST follow this EXACT schema. Do not add, remove, or rename any fields. Also, leave coords blank:

{
  "campus": "<Official school name as string>",
  "timezone": "<IANA timezone string, e.g. America/New_York>",
  "routes": [
    {
      "id": "<kebab-case slug from route name, e.g. safety-shuttle>",
      "name": "<Route name as printed on the schedule>",
      "color": "<Hex color if visible, otherwise null>",
      "stops": [
        {
          "id": "<kebab-case slug from stop name, e.g. drayer-hall>",
          "name": "<Stop name exactly as printed>",
          "coords": [],
          "arrivals": ["HH:MM", "HH:MM"]
        }
      ]
    }
  ],
  "hours": {
    "<lowercase full day name>": { "start": "HH:MM", "end": "HH:MM" }
  }
}

Rules:
1. STOPS: List in the order the shuttle visits them based on the first departure cycle.
2. ARRIVALS: Every scheduled time as a flat array in 24-hour "HH:MM" format. Convert AM/PM. Expand ranges into individual times.
3. COORDS: Approximate [latitude, longitude] using your geographic knowledge of the campus, rounded to 4 decimal places. Use null if unknown.
4. ROUTES: Separate object for each named route. If only one unnamed route, use id "safety-shuttle" and name "Safety Shuttle".
5. COLOR: Hex color if the document uses one for the route, otherwise null.
6. HOURS: Every operating day as a separate key using full lowercase day name. "start" is earliest departure, "end" is last arrival. Omit days with no service.
7. OUTPUT: ONLY the JSON object. No text before or after. No markdown. No code fences."""


def process(filename):
    filepath = os.path.join("ingestion", filename)
    ext = filename.lower().rsplit('.', 1)[-1]

    mime_types = {
        'pdf': 'application/pdf',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'webp': 'image/webp',
        'tiff': 'image/tiff',
        'bmp': 'image/bmp'
    }

    if ext not in mime_types:
        raise ValueError(f"Unsupported file type: {ext}")

    with open(filepath, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    
    response = litellm.completion(
        model="gemini/gemini-2.5-flash",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:{mime_types[ext]};base64,{b64}"}}
            ]
        }]
    )

    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    schedule = json.loads(text)

    output_path = os.path.join("ingestion", "schedule.json")
    with open(output_path, "w") as f:
        json.dump(schedule, f, indent=2)

    print(f"Saved to {output_path}")
    return schedule


if __name__ == "__main__":
    result = process("schedule.png")
    print(json.dumps(result, indent=2))