import io, os, aiohttp, discord
from discord.ext import commands
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

load_dotenv(override=True)

TOKEN = os.getenv("TOKEN")
RECEPCAO_ID = os.getenv("RECEPCAO_ID")

intents = discord.Intents.all()

bot = commands.Bot("!", intents=intents)

async def fetch_avatar(url:str) -> Image.Image:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.read()
        
        return Image.open(io.BytesIO(data)).convert("RGBA")

def make_circle(image:Image.Image, size:int):
    image = image.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)

    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)

    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(image, (0, 0), mask)

    return output

def build_welcome_image(avatar:Image, username:str, member_count:int) -> io.BytesIO:
    W, H = 800, 300
    AVATAR_SIZE = 180
    AVATAR_X, AVATAR_Y = 60, (H - AVATAR_SIZE) // 2

    bg = Image.new("RGB", (W, H), (23, 27, 48))
    draw = ImageDraw.Draw(bg)

    draw.rectangle([0, 0, 8, H], fill=(88, 101, 242))

    border_size = AVATAR_SIZE + 12
    border_x = AVATAR_X - 6
    border_Y = AVATAR_Y - 6

    draw.ellipse(
        [border_x, border_Y, border_x + border_size, border_Y + border_size],
        outline=(88, 101, 242),
        width=4
    )

    circle_avatar = make_circle(avatar, AVATAR_SIZE)
    bg.paste(circle_avatar, (AVATAR_X, AVATAR_Y), circle_avatar)

    try:
        font_big = ImageFont.truetype("arial.ttf", 42)
        font_medium = ImageFont.truetype("arial.ttf", 28)
        font_small = ImageFont.truetype("arial.ttf", 22)
    except IOError:
        font_big = ImageFont.load_default()
        font_medium = font_big
        font_small = font_big
    
    text_x = AVATAR_X + AVATAR_SIZE + 40

    draw.text((text_x, 70), "Bem-vindo(a)", font=font_medium, fill=(170, 170, 200))
    draw.text((text_x, 110), username, font=font_big, fill=(255, 255, 255))
    draw.text((text_x, 175), f"Você é o membro #{member_count}", font=font_small, fill=(140, 145, 180))

    draw.line([text_x, 162, W - 40, 162], fill=(60, 65, 100), width=1)

    buf = io.BytesIO()
    bg.save(buf, format="PNG")
    buf.seek(0)
    return buf

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}.")

@bot.event
async def on_member_join(member:discord.Member):
    recepcao_canal = bot.get_channel(RECEPCAO_ID)
    if not recepcao_canal:
        recepcao_canal = await bot.fetch_channel(RECEPCAO_ID)
    
    avatar_url = member.display_avatar.replace(format="png", size=256).url
    avatar_img = await fetch_avatar(avatar_url)

    image_buf = build_welcome_image(avatar_img, member.display_name, member.guild.member_count)

    file = discord.File(fp=image_buf, filename="welcome.png")
    await recepcao_canal.send(f"Bem vindo(a) ao servidor, {member.mention}! Leia as regras e aproveito sua estadia.", file=file)

bot.run(TOKEN)