"""Generate a macOS .icns icon for Starlink Incident Monitor."""

import math
import os
import subprocess

from PIL import Image, ImageDraw, ImageFilter

SIZE = 1024
img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# Background: radial gradient cyan -> purple -> dark blue
cx = cy = SIZE // 2
max_r = int(SIZE * math.sqrt(2) / 2)
for r in range(max_r, 0, -2):
    t = r / max_r
    # interpolation between 3 colors
    if t < 0.5:
        k = t / 0.5
        col = (
            int(52 + (91 - 52) * k),  # cyan -> blue
            int(231 + (140 - 231) * k),
            int(255 + (255 - 255) * k),
        )
    else:
        k = (t - 0.5) / 0.5
        col = (
            int(91 + (16 - 91) * k),  # blue -> dark
            int(140 + (22 - 140) * k),
            int(255 + (50 - 255) * k),
        )
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (255,))

# Rounded mask (squircle approx via rounded rectangle on transparent bg)
mask = Image.new("L", (SIZE, SIZE), 0)
md = ImageDraw.Draw(mask)
md.rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=SIZE * 0.22, fill=255)
out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
out.paste(img, (0, 0), mask)
img = out
d = ImageDraw.Draw(img)

# Glowing halo behind the dish
glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.ellipse([cx - 330, cy - 330, cx + 330, cy + 330], fill=(52, 231, 255, 90))
glow = glow.filter(ImageFilter.GaussianBlur(60))
img.alpha_composite(glow)
d = ImageDraw.Draw(img)


# Signal waves (concentric arcs above the dish)
def arc_cx(angle_start, angle_end, r, width, col):
    bbox = [cx - r, cy - r - 40, cx + r, cy + r - 40]
    d.arc(bbox, angle_start, angle_end, fill=col, width=width)


for r, w, a in [(190, 10, 120), (255, 8, 90), (320, 6, 60)]:
    arc_cx(200, 340, r, w, (255, 255, 255, a))

# Dish (plate): a flattened ellipse
dish_cx, dish_cy = cx, cy + 150
dish_w, dish_h = 360, 130
d.ellipse(
    [dish_cx - dish_w, dish_cy - dish_h, dish_cx + dish_w, dish_cy + dish_h],
    fill=(220, 240, 255, 255),
    outline=(52, 231, 255, 255),
    width=6,
)
# dish interior (concave)
d.ellipse(
    [
        dish_cx - dish_w + 24,
        dish_cy - dish_h + 28,
        dish_cx + dish_w - 24,
        dish_cy + dish_h - 28,
    ],
    fill=(30, 40, 80, 255),
)
# arm + LNB
d.line(
    [dish_cx, dish_cy - dish_h + 30, dish_cx, dish_cy - dish_h - 130],
    fill=(255, 255, 255, 230),
    width=12,
)
d.ellipse(
    [dish_cx - 26, dish_cy - dish_h - 158, dish_cx + 26, dish_cy - dish_h - 106],
    fill=(168, 114, 255, 255),
    outline=(255, 255, 255, 200),
    width=4,
)

# small satellite top-right
sat_x, sat_y = cx + 250, cy - 240
d.rectangle(
    [sat_x - 40, sat_y - 26, sat_x + 40, sat_y + 26],
    fill=(255, 255, 255, 240),
    outline=(52, 231, 255, 255),
    width=4,
)
# solar panels
d.rectangle(
    [sat_x - 110, sat_y - 14, sat_x - 42, sat_y + 14],
    fill=(20, 30, 60, 255),
    outline=(120, 150, 255, 255),
    width=3,
)
d.rectangle(
    [sat_x + 42, sat_y - 14, sat_x + 110, sat_y + 14],
    fill=(20, 30, 60, 255),
    outline=(120, 150, 255, 255),
    width=3,
)

img.save("icon.png")

# Build the .iconset then .icns
os.makedirs("StarlinkMonitor.iconset", exist_ok=True)
sizes = [16, 32, 64, 128, 256, 512, 1024]
for s in sizes:
    r = img.resize((s, s), Image.LANCZOS)
    r.save(f"StarlinkMonitor.iconset/icon_{s}x{s}.png")
    if s < 1024:
        r2 = img.resize((s * 2, s * 2), Image.LANCZOS)
        r2.save(f"StarlinkMonitor.iconset/icon_{s}x{s}@2x.png")
subprocess.run(  # nosec  # constant args, build-time only (B603,B607)
    ["iconutil", "-c", "icns", "StarlinkMonitor.iconset", "-o", "StarlinkMonitor.icns"],
    check=True,
)
print("✅ StarlinkMonitor.icns generated")
