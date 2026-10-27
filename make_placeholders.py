"""Генерирует временные обложки для кейсов (замени своими фото)."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent / "media"
OUT.mkdir(exist_ok=True)

CASES = [
    ("case_coffee.jpg", "Кофейня «Зёрна»", "Айдентика · 2025", (94, 67, 54), (222, 196, 170)),
    ("case_delivery.jpg", "Сервис «Быстро»", "Digital · 2024", (28, 30, 43), (255, 106, 61)),
    ("case_cosmetic.jpg", "Косметика «Soft»", "Упаковка · 2024", (240, 232, 227), (176, 138, 122)),
]

W, H = 1200, 900
FONT_BIG = "/usr/share/fonts/truetype/google/PlayfairDisplay.ttf"
FONT_SMALL = "/usr/share/fonts/truetype/google/Manrope.ttf"


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


for name, title, sub, bg, fg in CASES:
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    d.ellipse([W * 0.55, -H * 0.2, W * 1.4, H * 0.8], fill=fg)
    d.text((80, H * 0.35), title, font=font(FONT_BIG, 76), fill=fg)
    d.text((84, H * 0.35 + 110), sub.upper(), font=font(FONT_SMALL, 34), fill=fg)
    img.save(OUT / name, quality=88)
    print("saved", OUT / name)
