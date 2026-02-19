import os
import time
import uuid
from ast import literal_eval
from colorsys import hsv_to_rgb
from functools import lru_cache
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont, ImageOps

from StarManager.core.config import settings


@lru_cache(maxsize=8)
def _get_font(size: int) -> ImageFont.FreeTypeFont:
    path = os.path.join(
        settings.service.path,
        "src",
        "StarManager",
        "core",
        "media",
        "fonts",
        "statsimg_font_bold.ttf",
    )
    return ImageFont.truetype(path, size)


@lru_cache(maxsize=64)
def _load_template(pss: str, imglvl: str, prem: bool) -> Image.Image:
    prem_suffix = "" if prem else "n"
    template_path = os.path.join(
        settings.service.path,
        "src",
        "StarManager",
        "core",
        "media",
        "stats",
        pss,
        f"{imglvl}_{prem_suffix}p.png",
    )
    img = Image.open(template_path).convert("RGBA")
    return img


@lru_cache(maxsize=16)
def _load_icon(name: str) -> Image.Image:
    p = os.path.join(
        settings.service.path,
        "src",
        "StarManager",
        "core",
        "media",
        "stats",
        "icon",
        name,
    )
    return Image.open(p).convert("RGBA")


@lru_cache(maxsize=64)
def _hsv_color_for_level(level: int) -> Tuple[int, int, int]:
    h = (level - 1) / 50.0
    s = 0.65 + 0.25 * ((level % 5) / 4)
    v = 0.78 + 0.17 * ((level % 7) / 6)
    r, g, b = hsv_to_rgb(h, s, v)
    return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def _parse_color(color_raw, is_custom: bool, access_level: int, prem: bool):
    if color_raw and prem:
        try:
            if isinstance(color_raw, str):
                color = literal_eval(color_raw)
            else:
                color = tuple(color_raw)
            if len(color) >= 3:
                return tuple(int(c) for c in color[:3])
        except Exception:
            color = False
    if is_custom:
        return (
            _hsv_color_for_level(access_level)
            if 1 <= access_level <= 50
            else (84, 84, 84)
        )
    else:
        colors = {
            0: (84, 84, 84),
            1: (37, 72, 161),
            2: (67, 64, 238),
            3: (5, 0, 255),
            4: (56, 157, 48),
            5: (255, 107, 0),
            6: (87, 0, 155),
            7: (181, 86, 255),
            8: (255, 0, 0),
        }
        return colors.get(access_level, (84, 84, 84))


def createStatsImage(
    warns,
    messages,
    uid,
    access_level,
    is_custom,
    nickname,
    starcoins,
    last_activity,
    prem,
    xp,
    userlvl,
    reputation,
    reptop,
    name,
    mute,
    ban,
    lvl_name,
    neededxp,
    color,
    league,
) -> str:
    now = time.time()

    flags = []
    if mute > now:
        flags.append("m")
    if ban > now:
        flags.append("b")
    if warns > 0:
        flags.append("w")
    pss = "".join(flags) or "no"

    if userlvl < 25:
        imglvl = "1-25"
    elif userlvl < 50:
        imglvl = "25-50"
    elif userlvl < 75:
        imglvl = "50-75"
    else:
        imglvl = "75+"

    try:
        img = _load_template(pss, imglvl, prem > 0)
    except FileNotFoundError:
        img = Image.new("RGBA", (1200, 600), (30, 30, 30, 255))
    draw = ImageDraw.Draw(img)

    font = _get_font(24)
    lvlfont = _get_font(35 if userlvl < 100 else 30)
    fontsmall = _get_font(17)
    fontgrey = _get_font(15)
    pfont = _get_font(20)

    draw.text((107, 186), f"{messages}", font=font, fill=(255, 255, 255))
    draw.text((107, 260), f"{int(starcoins)}", font=font, fill=(255, 255, 255))
    draw.text((107, 335), f"{last_activity}", font=font, fill=(255, 255, 255))
    rep_fill = (180, 216, 167) if reputation >= 0 else (231, 154, 154)
    draw.text(
        (107, 410),
        f"{'+' if reputation > 0 else ''}{reputation} (#{reptop})",
        font=font,
        fill=rep_fill,
    )

    draw.text(
        (img.size[0] // 2, 323), f"{name}", font=font, fill=(255, 255, 255), anchor="ma"
    )
    if nickname:
        draw.text(
            (img.size[0] // 2, 366),
            f"{nickname}",
            font=font,
            fill=(255, 255, 255),
            anchor="ma",
        )

    box_color = _parse_color(color, is_custom, access_level, prem > 0)

    draw.text(
        (img.size[0] // 2, 408),
        f"{lvl_name}",
        font=font,
        fill=(255, 255, 255),
        anchor="ma",
    )

    new = Image.new("RGBA", img.size, (255, 255, 255, 0))
    center = img.size[0] // 2
    half_text = (font.size * len(lvl_name)) // 2 if lvl_name else 50
    max_half = int(img.size[0] / 4.5)

    left = max(center - half_text - 5, center - max_half)
    right = min(center + half_text + 5, center + max_half)

    overlay = ImageDraw.Draw(new)
    overlay.rounded_rectangle(
        [(left, 405.5), (right, 440.5)],
        fill=(0, 0, 0, 0),
        outline=box_color,
        width=3,
        radius=11,
    )
    img = Image.alpha_composite(img, new)
    draw = ImageDraw.Draw(img)

    draw.text((775, 285), f"{xp}", font=font, fill=(255, 255, 255), anchor="ma")

    if prem > now:
        days_left = int((prem - now) / 86400) + 1
        premfont = _get_font(30)
        x, y = 1010, 376
        draw.text(
            (x, y), f"{days_left}", font=premfont, fill=(255, 183, 67), anchor="ma"
        )
        draw.text((x, y + 30), "дней", font=premfont, fill=(255, 255, 255), anchor="ma")

    mute_minutes = max(1, int((mute - now) / 60) + 1) if mute > now else 0
    ban_days = max(1, int((ban - now) / 86400) + 1) if ban > now else 0

    if "m" in pss and "b" in pss and "w" in pss:
        draw.text(
            (221, 61),
            f"{mute_minutes} минут",
            font=pfont,
            fill=(255, 255, 255),
            anchor="la",
        )
        draw.text(
            (961, 61), f"{ban_days} дней", font=pfont, fill=(255, 255, 255), anchor="la"
        )
        draw.text(
            (634, 61), f"{warns}/3", font=pfont, fill=(255, 255, 255), anchor="la"
        )
    elif "b" in pss and "w" in pss:
        draw.text(
            (460, 60), f"{warns}/3", font=pfont, fill=(255, 255, 255), anchor="la"
        )
        draw.text(
            (770, 60), f"{ban_days} дней", font=pfont, fill=(255, 255, 255), anchor="la"
        )
    elif "m" in pss and "b" in pss:
        draw.text(
            (411, 60),
            f"{mute_minutes} минут",
            font=pfont,
            fill=(255, 255, 255),
            anchor="la",
        )
        draw.text(
            (770, 60), f"{ban_days} дней", font=pfont, fill=(255, 255, 255), anchor="la"
        )
    elif "m" in pss and "w" in pss:
        draw.text(
            (411, 59),
            f"{mute_minutes} минут",
            font=pfont,
            fill=(255, 255, 255),
            anchor="la",
        )
        draw.text(
            (810, 59), f"{warns}/3", font=pfont, fill=(255, 255, 255), anchor="la"
        )
    elif "m" in pss:
        xy = (586, 58) if prem > 0 else (572, 61)
        draw.text(
            xy, f"{mute_minutes} минут", font=pfont, fill=(255, 255, 255), anchor="la"
        )
    elif "b" in pss:
        draw.text(
            (600, 61), f"{ban_days} дней", font=pfont, fill=(255, 255, 255), anchor="la"
        )
    elif "w" in pss:
        xy = (634, 60) if prem > 0 else (650, 57)
        draw.text(xy, f"{warns}/3", font=pfont, fill=(255, 255, 255), anchor="la")

    x = 498
    y = 143
    height = 169
    width = 169
    fg = (67, 64, 238)
    progress = 0.0
    try:
        progress = float(xp) / float(xp + neededxp) if (xp + neededxp) > 0 else 0.0
    except Exception:
        progress = 0.0

    draw.arc(
        (x, y, x + width, y + height),
        start=-90,
        end=progress * 360 - 90,
        fill=fg,
        width=10,
    )
    draw.ellipse((x + 10, y + 10, x + width - 10, y + height - 10), fill=(36, 36, 36))

    ava_path = os.path.join(
        settings.service.path,
        "src",
        "StarManager",
        "core",
        "media",
        "temp",
        f"{uid}ava.jpg",
    )
    try:
        ava = Image.open(ava_path).convert("RGBA")
    except Exception:
        ava = Image.new("RGBA", (143, 143), (70, 70, 70, 255))

    ava = ImageOps.fit(ava, (143, 143), method=Image.Resampling.LANCZOS)
    mask = Image.new("L", ava.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0) + ava.size, fill=255)
    img.paste(ava, (511, 156), mask=mask)

    try:
        lvl_icon = _load_icon("dot.png")
        img.paste(lvl_icon, mask=lvl_icon)
    except Exception:
        pass

    draw.text((663, 158), f"{userlvl}", font=lvlfont, fill=(63, 63, 63), anchor="ma")

    draw.rectangle(((360, 250), (415, 270)), (38, 38, 38))
    draw.text(
        xy=(392, 249), text="ЛИГА", font=fontsmall, fill=(255, 255, 255), anchor="ma"
    )
    league_name = (
        settings.leagues.leagues[league - 1]
        if 1 <= league <= len(settings.leagues.leagues)
        else "—"
    )
    draw.text((392, 284.5), league_name, font=font, fill=(255, 255, 255), anchor="ma")

    try:
        rep = _load_icon("rep.png")
        img.paste(rep, (38, 382), mask=rep)
    except Exception:
        pass
    draw.text(
        xy=(151, 392),
        text="Репутация",
        font=fontgrey,
        fill=(113, 113, 113),
        anchor="ma",
    )

    try:
        coin = _load_icon("coin.png")
        img.paste(coin, (38, 231), mask=coin)
    except Exception:
        pass
    draw.text(
        xy=(162, 241),
        text="Star-монетки",
        font=fontgrey,
        fill=(113, 113, 113),
        anchor="ma",
    )

    out_dir = os.path.join(
        settings.service.path, "src", "StarManager", "core", "media", "temp"
    )
    os.makedirs(out_dir, exist_ok=True)
    filename = f"frame{uid}_{uuid.uuid4().hex}.png"
    path = os.path.join(out_dir, filename)
    img.save(path)
    return path
