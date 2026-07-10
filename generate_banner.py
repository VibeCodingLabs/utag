from PIL import Image, ImageDraw, ImageFont
import os

# Create directory
os.makedirs(os.path.expanduser('~/.github/assets'), exist_ok=True)

# Image dimensions
width = 1200
height = 630

# Colors for Midnight Blueprint Dark Mode
bg_color = "#0B1120" # Dark slate/blue
grid_color = "#1E293B" # Lighter blue for grid
text_color = "#38BDF8" # Light blue/cyan for text
title_color = "#F8FAFC" # White for title

# Create image
img = Image.new('RGB', (width, height), color=bg_color)
draw = ImageDraw.Draw(img)

# Draw grid
grid_size = 40
for x in range(0, width, grid_size):
    draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
for y in range(0, height, grid_size):
    draw.line([(0, y), (width, y)], fill=grid_color, width=1)

# Draw thicker grid lines every 4 cells
for x in range(0, width, grid_size * 4):
    draw.line([(x, 0), (x, height)], fill=grid_color, width=2)
for y in range(0, height, grid_size * 4):
    draw.line([(0, y), (width, y)], fill=grid_color, width=2)

# Load fonts
try:
    font_bold = ImageFont.truetype(os.path.expanduser('~/.fonts/Roboto-Bold.ttf'), 72)
    font_regular = ImageFont.truetype(os.path.expanduser('~/.fonts/Roboto-Regular.ttf'), 36)
except IOError:
    # Fallback if fonts are not available
    font_bold = ImageFont.load_default()
    font_regular = ImageFont.load_default()

# Text to draw
title_text = "Provider Agnostic Agent Handbook"
subtitle_text = "Midnight Blueprint Dark Mode - Design System"

# Calculate text bounding boxes to center it
title_bbox = draw.textbbox((0, 0), title_text, font=font_bold)
title_w = title_bbox[2] - title_bbox[0]
title_h = title_bbox[3] - title_bbox[1]

subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=font_regular)
subtitle_w = subtitle_bbox[2] - subtitle_bbox[0]
subtitle_h = subtitle_bbox[3] - subtitle_bbox[1]

# Draw text
draw.text(((width - title_w) / 2, (height - title_h) / 2 - 40), title_text, font=font_bold, fill=title_color)
draw.text(((width - subtitle_w) / 2, (height - subtitle_h) / 2 + 60), subtitle_text, font=font_regular, fill=text_color)

# Draw some blueprint-like elements (e.g., crosshairs in corners)
margin = 40
crosshair_len = 20
corners = [
    (margin, margin),
    (width - margin, margin),
    (margin, height - margin),
    (width - margin, height - margin)
]

for cx, cy in corners:
    draw.line([(cx - crosshair_len, cy), (cx + crosshair_len, cy)], fill=text_color, width=2)
    draw.line([(cx, cy - crosshair_len), (cx, cy + crosshair_len)], fill=text_color, width=2)
    draw.ellipse([(cx - 5, cy - 5), (cx + 5, cy + 5)], outline=text_color, width=2)

# Save image
output_path = os.path.expanduser('~/.github/assets/provider-agnostic-agent-handbook.png')
img.save(output_path)
print(f"Saved banner to {output_path}")
