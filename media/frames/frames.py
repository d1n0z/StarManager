from PIL import Image, ImageDraw, ImageFont

from config.config import PATH


def createFrame(framelvl: int, prem: int | str, wins: int | str, uid: int | str, userlvl: int | str, top: int | str,
                xp: int, neededxp: int, name: str):
    img = Image.open(f'{PATH}media/frames/frames.png')
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype(f'{PATH}media/fonts/framefont.ttf', 26)
    draw.text((1300, 128), f'{wins} Побед', font=font, fill=(255, 255, 255), anchor='ra')

    font = ImageFont.truetype(f'{PATH}media/fonts/framefont.ttf', 32)
    draw.text((1300, 163), f'{xp}  /  {neededxp} Exp', font=font, fill=(255, 255, 255), anchor='ra')
    draw.text((287, 163), f'Уровень {userlvl}  /  Top #{top}', font=font, fill=(255, 255, 255))
    draw.text((287, 40), f'{name}', font=font, fill=(255, 255, 255))

    ava = Image.open(f'{PATH}media/temp/{uid}ava.jpg')
    ava = ava.resize((132, 134))
    avamask_im = Image.new("L", ava.size, 0)  # noqa
    avadraw = ImageDraw.Draw(avamask_im)
    avadraw.ellipse((0, 0, 132, 134), fill=255)
    if framelvl != 1:
        avadraw.rectangle((0, 126, 200, 200), fill=0)
    img.paste(ava, (79, 68), mask=avamask_im)

    frame = Image.open(f'{PATH}media/frames/frame{framelvl}.png')
    img.paste(frame, (-1, 5), mask=frame)

    if prem:
        font = ImageFont.truetype(f'{PATH}media/fonts/framefont.ttf', 24)
        draw.text((1216, 58), f'{prem} Дней', font=font, fill=(255, 255, 255), anchor='mm')
        premiumimg = Image.open(f'{PATH}media/frames/premiumimg.png')
        img.paste(premiumimg, (1100, 41), mask=premiumimg)

    x = 276
    y = 202
    height = 223 - y
    width = 1286 - x
    fg = (82, 151, 255)
    bg = (56, 86, 130)
    progress = 1 - ((neededxp - xp) / 200)
    draw.rectangle((x + (height / 2), y, x + width + (height / 2), y + height), fill=bg, width=10)
    draw.ellipse((x + width, y, x + height + width, y + height), fill=bg)
    draw.ellipse((x, y, x + height, y + height), fill=bg)
    width = int(width * progress)

    draw.rectangle((x + (height / 2), y, x + width + (height / 2), y + height), fill=fg, width=10)
    draw.ellipse((x + width, y, x + height + width, y + height), fill=fg)
    draw.ellipse((x, y, x + height, y + height), fill=fg)

    img.save(f'{PATH}media/temp/frame{uid}.png')
    return f'{PATH}media/temp/frame{uid}.png'
