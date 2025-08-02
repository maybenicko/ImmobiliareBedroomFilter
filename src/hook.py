from dhooks import Webhook, Embed
from datetime import datetime
import json
from pathlib import Path


def send_house_hook(data):
    config_path = Path(__file__).parents[1] / 'config' / 'settings.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    webhook = cfg.get('webhook')
    hook = Webhook(webhook)

    now = datetime.utcnow().strftime('%d-%m-%Y')
    embed = Embed(
        color=0x202020,
        thumbnail_url=data['img']
    )
    embed.set_title(f":biting_lip: {data['title']} :biting_lip:", url=data['url'])
    embed.set_author(name="PiedeAIO - nicko.py",
                     icon_url="https://cdn.discordapp.com/attachments/799962707377127444/990984201664888912/bartFoto.PNG")
    embed.add_field(name="Price", value=data['price'])
    embed.add_field(name="Balcony", value=data['balcony'])
    embed.add_field(name="Price Per Room", value=f"€ {data['price_per_room']}/mese")
    embed.add_field(name="Bedrooms", value=data['bedrooms'])
    embed.add_field(name="Bathrooms", value=data['bathrooms'])
    embed.add_field(name="Square Meters", value=data['surface'])
    embed.set_footer(text=f"{now} • Powered by @PiedeAIO • {data['task_name']}",
                     icon_url="https://cdn.discordapp.com/attachments/799962707377127444/990984201664888912/bartFoto.PNG")

    hook.send(embed=embed)
