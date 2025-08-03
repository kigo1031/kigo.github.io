from PIL import Image, ImageDraw, ImageFont
import os

# Create a new image with white background and rounded corners
size = 32
img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
draw = ImageDraw.Draw(img)

# Draw rounded rectangle background
margin = 2
corner_radius = 6
# Draw rounded rectangle
def draw_rounded_rectangle(draw, xy, corner_radius, fill, outline=None, width=1):
    x0, y0, x1, y1 = xy
    draw.rectangle([x0 + corner_radius, y0, x1 - corner_radius, y1], fill=fill, outline=outline, width=width)
    draw.rectangle([x0, y0 + corner_radius, x1, y1 - corner_radius], fill=fill, outline=outline, width=width)
    draw.pieslice([x0, y0, x0 + corner_radius * 2, y0 + corner_radius * 2], 180, 270, fill=fill, outline=outline, width=width)
    draw.pieslice([x1 - corner_radius * 2, y0, x1, y0 + corner_radius * 2], 270, 360, fill=fill, outline=outline, width=width)
    draw.pieslice([x0, y1 - corner_radius * 2, x0 + corner_radius * 2, y1], 90, 180, fill=fill, outline=outline, width=width)
    draw.pieslice([x1 - corner_radius * 2, y1 - corner_radius * 2, x1, y1], 0, 90, fill=fill, outline=outline, width=width)

# Draw background
draw_rounded_rectangle(draw, [margin, margin, size-margin, size-margin], corner_radius, fill='white', outline='#e5e7eb', width=1)

# Draw K letter
try:
    # Try to use a system font
    font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
except:
    # Fallback to default font
    font = ImageFont.load_default()

# Draw K in the center
text = "K"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x = (size - text_width) // 2
y = (size - text_height) // 2 - 2
draw.text((x, y), text, fill='black', font=font)

# Save the image
img.save('/Users/gyeomkim/development/blog/kigo/assets/images/favicon.png')
print("Favicon created successfully!")
