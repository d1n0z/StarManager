import time
from ast import literal_eval

from PIL import Image, ImageDraw, ImageFont

from config.config import LEAGUE, PATH


async def createStatsImage(
    warns,
    messages,
    uid,
    access_level,
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
):
    pss = list("xxx")
    if warns > 0:
        pss[2] = "w"
    if ban > time.time():
        pss[1] = "b"
    if mute > time.time():
        pss[0] = "m"
    pss = "".join(pss).replace("x", "")
    if pss == "":
        pss = "no"

    if userlvl < 25:
        imglvl = "1-25"
    elif userlvl < 50:
        imglvl = "25-50"
    elif userlvl < 75:
        imglvl = "50-75"
    else:
        imglvl = "75+"

    img = Image.open(f"{PATH}media/stats/{pss}/{imglvl}_{'' if prem > 0 else 'n'}p.png")
    img = img.convert("RGBA")
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype(f"{PATH}media/fonts/statsimg_font_bold.ttf", 24)
    draw.text((107, 186), f"{messages}", font=font, fill=(255, 255, 255))
    draw.text((107, 260), f"{starcoins}", font=font, fill=(255, 255, 255))
    draw.text((107, 335), f"{last_activity}", font=font, fill=(255, 255, 255))
    draw.text(
        (107, 410),
        f"{'+' if reputation > 0 else ''}{reputation} (#{reptop})",
        font=font,
        fill=(180, 216, 167) if reputation >= 0 else (231, 154, 154),
    )

    draw.text(
        (img.size[0] // 2, 323), f"{name}", font=font, fill=(255, 255, 255), anchor="ma"
    )
    if nickname is not None:
        draw.text(
            (img.size[0] // 2, 366),
            f"{nickname}",
            font=font,
            fill=(255, 255, 255),
            anchor="ma",
        )

    if color:
        try:
            color = literal_eval(color)
        except Exception as _:
            color = False
    if not color:
        if access_level == 1:
            color = (37, 72, 161)
        elif access_level == 2:
            color = (67, 64, 238)
        elif access_level == 3:
            color = (5, 0, 255)
        elif access_level == 4:
            color = (56, 157, 48)
        elif access_level == 5:
            color = (255, 107, 0)
        elif access_level == 6:
            color = (87, 0, 155)
        elif access_level == 7:
            color = (181, 86, 255)
        elif access_level == 8:
            color = (255, 0, 0)
        else:
            color = (84, 84, 84)

    draw.text(
        (img.size[0] // 2, 408),
        f"{lvl_name}",
        font=font,
        fill=(255, 255, 255),
        anchor="ma",
    )

    new = Image.new("RGBA", img.size, (255, 255, 255, 0))
    ImageDraw.Draw(new).rounded_rectangle(
        [
            (img.size[0] // 2 - (font.size * len(lvl_name) // 2) - 5, 405.5),
            (img.size[0] // 2 + (font.size * len(lvl_name) // 2) + 5, 440.5),
        ],
        fill=(0, 0, 0, 0),
        outline=color,
        width=3,
        radius=11,
    )
    img = Image.alpha_composite(img, new)
    draw = ImageDraw.Draw(img)

    draw.text((775, 285), f"{xp}", font=font, fill=(255, 255, 255), anchor="ma")
    lvlfont = ImageFont.truetype(
        f"{PATH}media/fonts/statsimg_font_bold.ttf", 35 if userlvl < 100 else 30
    )
    fontsmall = ImageFont.truetype(f"{PATH}media/fonts/statsimg_font_bold.ttf", 17)
    fontgrey = ImageFont.truetype(f"{PATH}media/fonts/statsimg_font_bold.ttf", 15)

    if prem > 0:
        premfont = ImageFont.truetype(f"{PATH}media/fonts/statsimg_font_bold.ttf", 30)
        x, y = 1010, 376
        draw.text(
            (x, y),
            f"{int((prem - time.time()) / 86400) + 1}",
            font=premfont,
            fill=(255, 183, 67),
            anchor="ma",
        )
        draw.text((x, y + 30), "дней", font=premfont, fill=(255, 255, 255), anchor="ma")

    pfont = ImageFont.truetype(f"{PATH}media/fonts/statsimg_font_bold.ttf", 20)
    mute = int((mute - time.time()) / 60) + 1
    ban = int((ban - time.time()) / 86400) + 1
    if "mbw" in pss:
        draw.text(
            (221, 61), f"{mute} минут", font=pfont, fill=(255, 255, 255), anchor="la"
        )
        draw.text(
            (961, 61), f"{ban} дней", font=pfont, fill=(255, 255, 255), anchor="la"
        )
        draw.text(
            (634, 61), f"{warns}/3", font=pfont, fill=(255, 255, 255), anchor="la"
        )
    elif "bw" in pss:
        if prem > 0:
            draw.text(
                (460, 60), f"{warns}/3", font=pfont, fill=(255, 255, 255), anchor="la"
            )
            draw.text(
                (770, 60), f"{ban} дней", font=pfont, fill=(255, 255, 255), anchor="la"
            )
        else:
            draw.text(
                (460, 59), f"{warns}/3", font=pfont, fill=(255, 255, 255), anchor="la"
            )
            draw.text(
                (770, 59), f"{ban} дней", font=pfont, fill=(255, 255, 255), anchor="la"
            )
    elif "mb" in pss:
        if prem > 0:
            draw.text(
                (411, 60),
                f"{mute} минут",
                font=pfont,
                fill=(255, 255, 255),
                anchor="la",
            )
            draw.text(
                (770, 60), f"{ban} дней", font=pfont, fill=(255, 255, 255), anchor="la"
            )
        else:
            draw.text(
                (411, 59),
                f"{mute} минут",
                font=pfont,
                fill=(255, 255, 255),
                anchor="la",
            )
            draw.text(
                (770, 59), f"{ban} дней", font=pfont, fill=(255, 255, 255), anchor="la"
            )
    elif "mw" in pss:
        draw.text(
            (411, 59), f"{mute} минут", font=pfont, fill=(255, 255, 255), anchor="la"
        )
        draw.text(
            (810, 59), f"{warns}/3", font=pfont, fill=(255, 255, 255), anchor="la"
        )
    elif "m" in pss:
        if prem > 0:
            xy = (586, 58)
        else:
            xy = (572, 61)
        draw.text(xy, f"{mute} минут", font=pfont, fill=(255, 255, 255), anchor="la")
    elif "b" in pss:
        draw.text(
            (600, 61), f"{ban} дней", font=pfont, fill=(255, 255, 255), anchor="la"
        )
    elif "w" in pss:
        if prem > 0:
            xy = (634, 60)
        else:
            xy = (650, 57)
        draw.text(xy, f"{warns}/3", font=pfont, fill=(255, 255, 255), anchor="la")

    x = 498
    y = 143
    height = 169
    width = 169
    fg = (67, 64, 238)
    progress = xp / (xp + neededxp)

    draw.arc(
        (x, y, x + width, y + height),
        start=0 - 90,
        end=progress * 360 - 90,
        fill=fg,
        width=10,
    )
    draw.ellipse((x + 10, y + 10, x + width - 10, y + height - 10), fill=(36, 36, 36))

    ava = Image.open(f"{PATH}media/temp/{uid}ava.jpg")
    ava = ava.resize((143, 143))
    avamask_im = Image.new("L", ava.size)
    avadraw = ImageDraw.Draw(avamask_im)
    avadraw.ellipse((0, 0, 143, 143), fill=255)
    img.paste(ava, (511, 156), mask=avamask_im)
    lvl = Image.open(f"{PATH}media/stats/icon/dot.png")
    img.paste(lvl, mask=lvl)

    draw.text((663, 158), f"{userlvl}", font=lvlfont, fill=(63, 63, 63), anchor="ma")

    draw.rectangle(((360, 250), (415, 270)), (38, 38, 38))
    draw.text(
        xy=(392, 249), text="ЛИГА", font=fontsmall, fill=(255, 255, 255), anchor="ma"
    )
    draw.text(
        (392, 284.5), LEAGUE[league - 1], font=font, fill=(255, 255, 255), anchor="ma"
    )

    draw.rectangle(((100, 390), (220, 410)), (29, 29, 29))
    draw.rectangle(((40, 380), (100, 450)), (29, 29, 29))
    rep = Image.open(f"{PATH}media/stats/icon/rep.png")
    img.paste(rep, (38, 382), mask=rep)
    draw.text(
        xy=(151, 392),
        text="Репутация",
        font=fontgrey,
        fill=(113, 113, 113),
        anchor="ma",
    )

    draw.rectangle(((100, 390 - 151), (260, 410 - 151)), (29, 29, 29))
    draw.rectangle(((40, 380 - 151), (100, 450 - 151)), (29, 29, 29))
    coin = Image.open(f"{PATH}media/stats/icon/coin.png")
    img.paste(coin, (38, 382 - 151), mask=coin)
    draw.text(
        xy=(162, 392 - 151),
        text="Star-монетки",
        font=fontgrey,
        fill=(113, 113, 113),
        anchor="ma",
    )

    img.save(f"{PATH}media/temp/frame{uid}.png")
    return f"{PATH}media/temp/frame{uid}.png"


if __name__ == "__main__":
    import asyncio

    asyncio.run(
        createStatsImage(
            0,
            123,
            746110579,
            8,
            "test",
            123,
            123,
            time.time() + 123 * 86400,
            123,
            123,
            123,
            123,
            "Копытов Илья",
            0,
            0,
            "dev",
            750,
            None,
            1,
        )
    )
