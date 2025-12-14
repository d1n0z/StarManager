from colorsys import hsv_to_rgb
from PIL import Image, ImageDraw, ImageFont
import math

MAX_LEVEL = 50
SWATCH_SIZE = 100
PADDING = 8
COLUMNS = 10


def hsv_color_for_level(level: int, max_level=MAX_LEVEL):
    h = (level - 1) / max_level
    s = 0.65 + 0.25 * ((level % 5) / 4)
    v = 0.78 + 0.17 * ((level % 7) / 6)
    r, g, b = hsv_to_rgb(h, s, v)
    return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def text_color_for_bg(rgb):
    r, g, b = rgb
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    return (0, 0, 0) if lum > 160 else (255, 255, 255)


rows = math.ceil(MAX_LEVEL / COLUMNS)
width = COLUMNS * SWATCH_SIZE + (COLUMNS + 1) * PADDING
height = rows * SWATCH_SIZE + (rows + 1) * PADDING + 10

img = Image.new("RGB", (width, height), (250, 250, 250))
draw = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype("DejaVuSans.ttf", 14)
except Exception:
    font = ImageFont.load_default()

for i in range(1, MAX_LEVEL + 1):
    col = (i - 1) % COLUMNS
    row = (i - 1) // COLUMNS
    x = PADDING + col * (SWATCH_SIZE + PADDING)
    y = PADDING + row * (SWATCH_SIZE + PADDING)
    color = hsv_color_for_level(i)
    draw.rectangle([x, y, x + SWATCH_SIZE, y + SWATCH_SIZE], fill=color)
    label = f"{i} {rgb_to_hex(color)}"
    tc = text_color_for_bg(color)
    bbox = draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    tx = x + 6
    ty = y + SWATCH_SIZE - text_h - 6
    draw.text((tx, ty), label, fill=tc, font=font)

out = "colors_preview.png"
img.save(out)
print(f"Saved preview to {out}")
