"""Generate the PNG icons referenced by the web app manifest."""
import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "site" / "static"
SITE_NAME = json.loads((ROOT / "site_config.json").read_text(encoding="utf-8"))["site_name"]


def icon(size):
    scale = 4
    image = Image.new("RGB", (size * scale, size * scale), "#4d6a38")
    draw = ImageDraw.Draw(image)
    unit = size * scale / 64

    def xy(points):
        return tuple(round(value * unit) for value in points)

    if SITE_NAME.endswith("English"):
        cream = "#fbfaf3"
        width = max(3, round(4 * unit))
        draw.line(xy((16, 47, 16, 18, 20, 14, 49, 14, 49, 48, 21, 48)),
                  fill=cream, width=width, joint="curve")
        draw.arc(xy((12, 44, 24, 56)), 90, 270, fill=cream, width=width)
        draw.line(xy((25, 24, 42, 24)), fill=cream, width=width)
        draw.line(xy((25, 33, 38, 33)), fill=cream, width=width)
    else:
        pale = "#f3efdd"
        light = "#a8c270"
        for box in ((18, 12, 46, 40), (10, 24, 32, 46), (32, 24, 54, 46), (19, 28, 45, 54)):
            draw.ellipse(xy(box), fill=pale)
        for box in ((24, 17, 40, 33), (14, 28, 26, 40), (38, 28, 50, 40)):
            draw.ellipse(xy(box), fill=light)

    return image.resize((size, size), Image.Resampling.LANCZOS)


for icon_size, filename in ((180, "apple-touch-icon.png"),
                            (192, "pwa-icon-192.png"),
                            (512, "pwa-icon-512.png")):
    icon(icon_size).save(STATIC / filename, optimize=True)
    print(f"wrote {filename} ({icon_size}x{icon_size})")
