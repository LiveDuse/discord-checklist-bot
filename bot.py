import discord
from discord.ext import commands

import os
TOKEN = os.getenv('DISCORD_TOKEN')
OWNER_IDS = [238003628017844224]  # Replace with your Discord user IDs. Separate with , if more than one
GUILD_ID = 1158906912402833408  # Replace with your Discord server (guild) ID
CHANNEL_ID = 1366469784912265358  # Replace with the channel ID where you want the checklist posted

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

checklist = []
checklist_status = []
checklist_title = ""
setup_mode = False
awaiting_title = False
current_setup_user = None

class ChecklistView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for idx, item in enumerate(checklist):
            self.add_item(CheckButton(label=item, index=idx))

class CheckButton(discord.ui.Button):
    def __init__(self, label, index):
        symbol = "✅" if checklist_status[index] else "⬜"
        super().__init__(label=f"{symbol} {label}", style=discord.ButtonStyle.secondary, row=index//5)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        checklist_status[self.index] = not checklist_status[self.index]
        await interaction.response.edit_message(content=f"**{checklist_title}**", view=ChecklistView())

@bot.command()
async def startchecklist(ctx):
    global checklist, checklist_status, setup_mode, current_setup_user, awaiting_title, checklist_title
    if ctx.author.id not in OWNER_IDS:
        return

    checklist = []
    checklist_status = []
    checklist_title = ""
    setup_mode = True
    awaiting_title = True
    current_setup_user = ctx.author.id
    user = await bot.fetch_user(ctx.author.id)
    await user.send("Checklist setup started! Please send the title for your checklist.")

@bot.command()
async def savechecklist(ctx):
    global checklist_status, setup_mode, current_setup_user, awaiting_title
    if ctx.author.id not in OWNER_IDS:
        return

    if not checklist:
        await ctx.send("Checklist is empty. Please add items before saving.")
        return

    checklist_status = [False for _ in checklist]
    setup_mode = False
    current_setup_user = None
    awaiting_title = False

    guild = bot.get_guild(GUILD_ID)
    channel = guild.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(content=f"**{checklist_title}**", view=ChecklistView())
    else:
        await ctx.send("Failed to find the channel to post the checklist.")

@bot.command()
async def editchecklist(ctx):
    global setup_mode, current_setup_user, awaiting_title
    if ctx.author.id not in OWNER_IDS:
        return
    setup_mode = True
    awaiting_title = True
    current_setup_user = ctx.author.id
    await ctx.send("Checklist edit mode: Please send the new title first.")

@bot.command()
async def undo(ctx):
    global checklist
    if ctx.author.id not in OWNER_IDS:
        return

    if setup_mode and isinstance(ctx.channel, discord.DMChannel):
        if checklist:
            removed_item = checklist.pop()
            await ctx.send(f"Removed last item: **{removed_item}**")
        else:
            await ctx.send("There are no items to undo.")
    else:
        await ctx.send("You can only undo during checklist setup in DM.")

@bot.event
async def on_message(message):
    global checklist, setup_mode, current_setup_user, awaiting_title, checklist_title
    if message.author == bot.user:
        return

    if setup_mode and message.author.id == current_setup_user:
        if isinstance(message.channel, discord.DMChannel):
            if awaiting_title and not message.content.startswith("!"):
                checklist_title = message.content.strip()
                awaiting_title = False
                await message.channel.send("Title set! Now send checklist items one-by-one. Type `!savechecklist` when done.")
            elif not awaiting_title and not message.content.startswith("!"):
                checklist.append(message.content.strip())
                await message.channel.send(f"Added: **{message.content.strip()}**")
            else:
                await bot.process_commands(message)
        else:
            await bot.process_commands(message)
    else:
        await bot.process_commands(message)

bot.run(TOKEN)
