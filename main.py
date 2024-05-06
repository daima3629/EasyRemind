import discord
from dataclasses import dataclass
import datetime
from typing import Optional

import discord.ext
import discord.ext.tasks

import secret

intents = discord.Intents.none()
intents.guilds = True
intents.guild_messages = True
intents.members = True
intents.message_content = True
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


@dataclass
class RemindInfo:
    time: datetime.datetime
    user: discord.User | discord.Member
    message: discord.Message
    memo: Optional[str]


reminds: list[RemindInfo] = []


class InputWhenReminds(discord.ui.Modal, title="リマインドする日付"):
    def __init__(self, message: discord.Message):
        super().__init__()
        self.message = message

    date = discord.ui.TextInput(
        label="リマインドする日を入力してください(数字８桁)",
        placeholder="20240101",
        min_length=8,
        max_length=8
    )

    time = discord.ui.TextInput(
        label="リマインドする時間を入力してください(数字4桁)",
        placeholder="1300",
        min_length=4,
        max_length=4
    )

    memo = discord.ui.TextInput(
        label="メモ(省略可)",
        style=discord.TextStyle.long,
        max_length=1000,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        time = datetime.datetime.strptime(self.date.value + self.time.value, "%Y%m%d%H%M")
        time = time.astimezone(datetime.timezone(datetime.timedelta(hours=9)))
        info = RemindInfo(time, interaction.user, self.message, self.memo.value)
        reminds.append(info)
        await interaction.response.send_message(
            f"設定しました。<t:{int(time.timestamp())}>にDMでリマインドします。",
            ephemeral=True
        )


@client.event
async def on_ready():
    await tree.sync()
    remind_loop.start()


@tree.context_menu(name="リマインドする")
async def remind(interaction: discord.Interaction, message: discord.Message):
    await interaction.response.send_modal(InputWhenReminds(message))


@discord.ext.tasks.loop(seconds=10)
async def remind_loop():
    now = datetime.datetime.now()
    now = now.astimezone(datetime.timezone(datetime.timedelta(hours=9)))
    targets: list[RemindInfo] = []
    for r in reminds:
        if now > r.time:
            targets.append(r)
    
    for t in targets:
        text = f"リマインド: {t.message.author.display_name}さんのメッセージ\nメモ:\n{t.memo}"
        embed = discord.Embed(
            color=discord.Color.blue(),
            description=t.message.content,
            timestamp=t.message.created_at
        )
        embed.set_author(name=t.message.author.display_name, icon_url=t.message.author.display_icon)
        dm = await t.user.create_dm()
        await dm.send(text, embed=embed)

        reminds.remove(t)


client.run(secret.DISCORD_TOKEN)
