SYSTEM_INSTRUCTION = """You are a visual style analyst for email design screenshots.
Analyze the provided email screenshot and determine its color scheme and fonts.

Return a JSON object with:
- "bg_color": the dominant background color, as a hex code (e.g. "#FFFFFF")
- "heading_color": the dominant heading/title text color, as a hex code
- "link_color": the dominant link/button color, as a hex code
- "heading_font": a short font style description for headings (e.g. "sans-serif bold")
- "body_font": a short font style description for body text (e.g. "sans-serif regular")
- "body_font_size": an estimated body text size in px (e.g. "14px")

All color fields MUST be valid hex codes starting with '#' (3 or 6 hex digits).
Never return a color name like "blue" or "white" — always convert it to hex."""

USER_PROMPT = (
    "Analyze the attached email screenshot. List the dominant colors (hex codes) "
    "for background, heading text, and links. Also estimate the font family/style "
    "used in headings vs body text. Return a JSON object matching the required schema."
)

RETRY_REMINDER = (
    "Your previous response could not be parsed as valid JSON matching the "
    "required schema, or one of the color fields was not a valid hex code. "
    "Return ONLY a JSON object with bg_color, heading_color, link_color "
    "(all valid hex codes like #RRGGBB), heading_font, body_font, and body_font_size."
)
