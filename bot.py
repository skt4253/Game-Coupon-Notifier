import os

import discord
from discord import app_commands

from coupon import COLOR, EMPTY_MESSAGE, TITLE, build, overflow_footer


class Bot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


bot = Bot()


@bot.tree.command(name="쿠폰", description="호요버스 쿠폰 교환 링크 생성")
@app_commands.describe(
    원신="코드들 (공백/쉼표 구분)",
    스타레일="코드들 (공백/쉼표 구분)",
    젠레스="코드들 (공백/쉼표 구분)",
)
async def coupon(
    inter: discord.Interaction,
    원신: str | None = None,
    스타레일: str | None = None,
    젠레스: str | None = None,
):
    fields, buttons, overflow = build({"genshin": 원신, "hsr": 스타레일, "zzz": 젠레스})
    if not fields:
        await inter.response.send_message(EMPTY_MESSAGE, ephemeral=True)
        return

    embed = discord.Embed(title=TITLE, color=COLOR)
    for name, value in fields:
        embed.add_field(name=name, value=value, inline=False)
    if overflow:
        embed.set_footer(text=overflow_footer())

    view = discord.ui.View()
    for label, url in buttons:
        view.add_item(discord.ui.Button(label=label, url=url))

    await inter.response.send_message(embed=embed, view=view)


if __name__ == "__main__":
    bot.run(os.environ["DISCORD_TOKEN"])
