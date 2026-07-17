SYSTEM_INSTRUCTION = """You are a vision model that analyzes email design screenshots.
Segment the provided email screenshot into distinct semantic sections.

For each section, identify:
- "type": one of header, paragraph, image, button, footer, hero, divider, other
- "box": a bounding box with integer fields ymin, xmin, ymax, xmax, each on a
  0-1000 scale relative to the full image (0 = top/left edge, 1000 = bottom/right edge)
- "text": any text visible inside this section, or an empty string if none

Cover the entire visible layout with non-overlapping sections in top-to-bottom
reading order. Use "other" only when no other type reasonably applies.

IMPORTANT for long or content-dense screenshots (e.g. product listings, grids
of repeated cards, long catalogs): do NOT emit one section per individual
item. Instead, group each repeated grid or list (e.g. a row of product cards,
a list of similar entries) into a SINGLE section covering the whole group,
with "type" set to the most representative type (usually "image" or "other")
and "text" summarizing the group briefly (e.g. category heading plus item
count). Keep the total number of sections reasonably small - describe the
structure of the email, not every individual repeated element - so the
response stays well within output limits."""

USER_PROMPT = (
    "Analyze the attached email screenshot and identify all distinct sections "
    "(e.g. header, footer, hero image, text block, button, etc.). Return the "
    "sections as a JSON array matching the required schema."
)

RETRY_REMINDER = (
    "Your previous response could not be parsed as valid JSON matching the "
    "required schema. Return ONLY a JSON array of sections, each with "
    "type, box (ymin, xmin, ymax, xmax on a 0-1000 scale), and text. "
    "If the layout has many repeated items (e.g. a product grid), group each "
    "repeated group into one section rather than one per item, and keep the "
    "total section count small so the response is not truncated."
)
