import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
from openai_chat import get_joke, query_huggingface, mood, generate_image, get_citation, get_quote
import time
from collections import defaultdict
import io

from database import (
    add_user, log_command_usage, log_user_mood,
    get_user_stats, get_server_stats, reset_user_mood, get_user_mood
)

load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


cooldowns = defaultdict(lambda: defaultdict(float))


def is_on_cooldown(user_id, command_name, cooldown_seconds):
    now = time.time()
    if now < cooldowns[user_id][command_name]:
        remaining = cooldowns[user_id][command_name] - now
        return True, round(remaining, 1)
    cooldowns[user_id][command_name] = now + cooldown_seconds
    return False, 0


MOOD_SETTINGS = {
    "happy": {"color": 0xFEE75C, "prefix": "🌟", "style": "upbeat and positive", "typing_emoji": "✍️"},
    "sad": {"color": 0x3498DB, "prefix": "☔", "style": "compassionate and gentle", "typing_emoji": "💬"},
    "angry": {"color": 0xE74C3C, "prefix": "⚡", "style": "calming and diplomatic", "typing_emoji": "✋"},
    "neutral": {"color": 0x2ECC71, "prefix": "🐸", "style": "neutral but friendly", "typing_emoji": "🤔"},
    "excited": {"color": 0xE91E63, "prefix": "🚀", "style": "energetic and enthusiastic", "typing_emoji": "⚡"},
    "anxious": {"color": 0x9B59B6, "prefix": "🧘", "style": "reassuring and clear", "typing_emoji": "🌀"}
}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.event
async def on_member_join(member):
    try:
        reset_user_mood(member.id)
        add_user(member.id, member.name)
        channel = member.guild.text_channels[0]
        if not channel.permissions_for(member.guild.me).send_messages:
            return

        embed = discord.Embed(
            title=f"🐸 Welcome to {member.guild.name}, {member.name}!",
            description=(
                "I'm Pepe, your friendly AI assistant!\n\n"
                "Here are some things you can do:\n"
                "• Use `/help` to see all commands\n"
                "• Try `/ask` to ask me anything\n"
                "• Need a laugh? Use `/joke`\n"
                "• Set your mood with `/setmood`\n\n"
                "Enjoy your stay! 🎉"
            ),
            color=0x2ECC71
        )
        if member.guild.icon:
            embed.set_thumbnail(url=member.guild.icon.url)
        await channel.send(embed=embed)
    except Exception as e:
        print(f"Error sending welcome message: {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    add_user(message.author.id, message.author.name)

# SLASH COMMANDS

@bot.tree.command(name="ping", description="🏓 Check if Pepe is alive.")
async def ping(interaction: discord.Interaction):
    log_command_usage(interaction.user.id, "ping")
    await interaction.response.send_message("Pong!")

@bot.tree.command(name="joke", description="😁 Need a laugh? Pepe delivers a random (bad) joke.")
async def joke(interaction: discord.Interaction):
    log_command_usage(interaction.user.id, "joke")
    joke_text = get_joke()
    await interaction.response.send_message(joke_text)

@bot.tree.command(name="about", description="📖 Learn more about Pepe AI.")
async def about(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🐸 About Pepe AI",
        description=(
            "Pepe AI is your friendly, AI-powered assistant here to make your Discord experience more fun and interactive! "
            "From mood management to generating art and even sharing random jokes, Pepe is always ready to assist.\n\n"
            "**Key Features:**\n"
            "• Mood Management\n"
            "• AI Chat & Art\n"
            "• User Stats\n"
            "• Server Friendly\n\n"
            "Pepe AI is here to keep your server fun and engaging! 🎉"
        ),
        color=0x00BFFF
    )
    embed.set_footer(text="🐸 Frogs and AI — Together at last!")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ask", description="💬 Ask Pepe anything.")
async def ask(interaction: discord.Interaction, question: str):
    on_cooldown, seconds = is_on_cooldown(interaction.user.id, "ask", 10)
    if on_cooldown:
        await interaction.response.send_message(f"⏳ You're on cooldown. Try again in {seconds}s.", ephemeral=True)
        return
    log_command_usage(interaction.user.id, "ask")
    user_mood = get_user_mood(interaction.user.id) or mood(question)
    props = MOOD_SETTINGS.get(user_mood, MOOD_SETTINGS["neutral"])

    await interaction.response.defer()
    reply = query_huggingface(f"Answer in a {props['style']} tone. {question}. Keep it short.")
    embed = discord.Embed(
        title=f"{props['prefix']} Pepe's Response",
        description=reply[:2048],
        color=props["color"]
    )
    embed.set_footer(text=f"🤖 Mood: {user_mood}")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="image", description="🎨 Turn your words into AI art!")
async def image(interaction: discord.Interaction, prompt: str):
    on_cooldown, seconds = is_on_cooldown(interaction.user.id, "image", 10)
    if on_cooldown:
        await interaction.response.send_message(f"⏳ You're on cooldown. Try again in {seconds}s.", ephemeral=True)
        return
    
    log_command_usage(interaction.user.id, "image")
    await interaction.response.defer()
    image_data = await generate_image(prompt)

    if not image_data:
        await interaction.followup.send("❌ Couldn't generate image.")
        return

    with io.BytesIO(image_data) as image_binary:
        await interaction.followup.send(file=discord.File(image_binary, "pepe_art.png"))

@bot.tree.command(name="invite", description="🔗 Invite Pepe AI to your server.")
async def invite(interaction: discord.Interaction):
    permissions = 277025770560
    invite_url = f"https://discord.com/oauth2/authorize?client_id={bot.user.id}&permissions={permissions}&scope=bot%20applications.commands"
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Invite Me", url=invite_url, emoji="➕"))
    embed = discord.Embed(
        title="🔗 Invite Pepe AI",
        description="Click below to invite Pepe with recommended permissions.",
        color=0x2ECC71
    )
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="setmood", description="🎭 Set your current mood.")
async def setmood(interaction: discord.Interaction, mood_type: str):
    log_command_usage(interaction.user.id, "setmood")
    mood_type = mood_type.lower()
    if mood_type not in MOOD_SETTINGS:
        await interaction.response.send_message(f"Invalid mood! Choose from: {', '.join(MOOD_SETTINGS)}")
        return
    log_user_mood(interaction.user.id, mood_type)
    props = MOOD_SETTINGS[mood_type]
    await interaction.response.send_message(f"{props['prefix']} Mood set to **{mood_type}**!")

@bot.tree.command(name="resetmood", description="🔄 Reset mood to auto-detection.")
async def resetmood(interaction: discord.Interaction):
    log_command_usage(interaction.user.id, "resetmood")
    reset_user_mood(interaction.user.id)
    await interaction.response.send_message("🔄 Mood auto-detection re-enabled!")

@bot.tree.command(name="mymood", description="😊 Check your current mood.")
async def mymood(interaction: discord.Interaction):
    log_command_usage(interaction.user.id, "mymood")
    current = get_user_mood(interaction.user.id)
    if current:
        props = MOOD_SETTINGS[current]
        await interaction.response.send_message(f"{props['prefix']} Your mood is set to **{current}**")
    else:
        await interaction.response.send_message("🐸 Mood is auto-detected!")

@bot.tree.command(name="stats", description="📊 View your usage stats.")
async def stats(interaction: discord.Interaction):
    log_command_usage(interaction.user.id, "stats")
    user_data = get_user_stats(interaction.user.id)
    if not user_data:
        await interaction.response.send_message("🐸 No stats yet.")
        return

    embed = discord.Embed(title=f"📊 Stats for {interaction.user.name}", color=0x00BFFF)
    embed.add_field(name="💬 Messages", value=user_data.get("message_count", 0))
    embed.add_field(name="📅 Join Date", value=user_data["join_date"].strftime("%Y-%m-%d"))
    if user_data.get("top_commands"):
        top = "\n".join(f"• `{c['command_name']}`: {c['usage_count']}x" for c in user_data["top_commands"])
        embed.add_field(name="🏆 Top Commands", value=top, inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="serverstats", description="📈 View server-wide stats.")
async def serverstats(interaction: discord.Interaction):
    stats = get_server_stats()
    embed = discord.Embed(title="📊 Server Stats", color=0x9B59B6)
    embed.add_field(name="👥 Total Users", value=stats["total_users"])
    embed.add_field(name="💬 Total Messages", value=stats["total_messages"])
    if stats.get("most_active_user"):
        u = stats["most_active_user"]
        embed.add_field(name="🏆 Most Active", value=f"{u['username']} ({u['message_count']} messages)")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="quote", description="📜 Get an inspirational quote.")
async def quote(interaction: discord.Interaction, topic: str = None):
    log_command_usage(interaction.user.id, "quote")
    text = get_quote(topic)

    if text.startswith("⚠️"):
        await interaction.response.send_message(text)
        return

    if "—" in text:
        quote_text, author = map(str.strip, text.split("—", 1))
    else:
        quote_text = text
        author = "Unknown"

    embed = discord.Embed(
        title="📜 Inspirational Quote",
        description=quote_text,
        color=0x95a5a6
    )
    embed.set_footer(text=f"— {author}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="cite", description="📚 Get an academic citation.")
async def cite(interaction: discord.Interaction, topic: str):
    log_command_usage(interaction.user.id, "cite")
    citation = get_citation(topic)
    await interaction.response.send_message(citation)

@bot.tree.command(name="compliment", description="💖 Receive a compliment!")
async def compliment(interaction: discord.Interaction, request: str = None):
    log_command_usage(interaction.user.id, "compliment")
    user_mood = get_user_mood(interaction.user.id) or "neutral"
    props = MOOD_SETTINGS.get(user_mood, MOOD_SETTINGS["neutral"])
    await interaction.response.defer()
    prompt = f"Give a {props['style']} compliment"
    if request:
        prompt += f" related to: {request}"
    prompt += ". Keep it under 1 sentence."
    reply = query_huggingface(prompt)
    embed = discord.Embed(
        description=f"💖 **Compliment for {interaction.user.name}:**\n\n{reply}",
        color=props["color"]
    )
    embed.set_footer(text=f"{props['prefix']} Pepe thinks you're awesome!")
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="explain", description="🧠 Get a clear explanation of any topic.")
async def explain(interaction: discord.Interaction, topic: str):
    log_command_usage(interaction.user.id, "explain")
    user_mood = get_user_mood(interaction.user.id) or "neutral"
    props = MOOD_SETTINGS.get(user_mood, MOOD_SETTINGS["neutral"])

    await interaction.response.defer()
    prompt = f"Explain in a {props['style']} tone: {topic}. Keep it clear and concise."
    explanation = query_huggingface(prompt)

    embed = discord.Embed(
        title=f"{props['prefix']} Here's the explanation",
        description=explanation[:2048],
        color=props["color"]
    )
    embed.set_footer(text=f"🤖 Mood: {user_mood}")
    await interaction.followup.send(embed=embed)



@bot.tree.command(name="help", description="📚 Get help with commands.")
@app_commands.describe(command_name="(Optional) The command you want help with")
async def help(interaction: discord.Interaction, command_name: str = None):
    if command_name:
        # Try to get the command from the app_commands tree
        command = next((cmd for cmd in bot.tree.walk_commands() if cmd.name == command_name.lower()), None)
        if not command:
            await interaction.response.send_message(f"❌ Command `{command_name}` not found.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"🛠 Help: /{command.name}",
            description=command.description or "No description available.",
            color=0x4d8000
        )

        if command.parameters:
            args = "\n".join(
                f"• `{p.name}`: {p.description or 'No description'}"
                for p in command.parameters
            )
            embed.add_field(name="Arguments", value=args, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        # General help menu
        embed = discord.Embed(
            title="🐸 Pepe AI - Help Menu",
            description="Here’s what I can do! Use `/` to see commands or scroll below.",
            color=0x00FF7F
        )
        embed.add_field(
            name="🤖 AI Features",
            value=(
                "`/ask` — Ask Pepe anything\n"
                "`/image` — Generate AI art\n"
                "`/quote` — Inspirational quote\n"
                "`/cite` — Academic citation\n"
                "`/compliment` — Custom compliment\n"
                "`/explain` — Explain any topic"
            ),
            inline=False
        )

        embed.add_field(
            name="🎉 Fun & Utility",
            value=(
                "`/ping` — Check if I'm alive\n"
                "`/joke` — Get a random joke\n"
                "`/invite` — Get my invite link"
            ),
            inline=False
        )

        embed.add_field(
            name="🎭 Mood Management",
            value=(
                "`/setmood` — Set your mood\n"
                "`/resetmood` — Use auto-detection\n"
                "`/mymood` — View current mood"
            ),
            inline=False
        )

        embed.add_field(
            name="📊 Stats",
            value=(
                "`/stats` — Your usage stats\n"
                "`/serverstats` — Server-wide stats"
            ),
            inline=False
        )

        embed.set_footer(text="🐸 Pepe AI | Use `/help [command]` for detailed help")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        

# ERRORS
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("🚫 You don't have permission to do that.", ephemeral=True)
    elif isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message("⏳ That command is on cooldown. Try again later.", ephemeral=True)
    elif isinstance(error, app_commands.MissingRequiredArgument):
        await interaction.response.send_message("⚠️ Missing required argument.", ephemeral=True)
    elif isinstance(error, app_commands.CommandInvokeError):
        await interaction.response.send_message(f"💥 Something went wrong: `{error.original}`", ephemeral=True)
    else:
        await interaction.response.send_message("❌ An unexpected error occurred.", ephemeral=True)


# AUTO COMPLETES

@setmood.autocomplete("mood_type")
async def mood_autocomplete(interaction: discord.Interaction, current: str):
    moods = [m for m in MOOD_SETTINGS if current.lower() in m]
    return [app_commands.Choice(name=m, value=m) for m in moods]


@help.autocomplete("command_name")
async def help_autocomplete(interaction: discord.Interaction, current: str):
    matches = [
        cmd.name for cmd in bot.tree.walk_commands()
        if current.lower() in cmd.name
    ]
    return [app_commands.Choice(name=name, value=name) for name in matches[:25]]



# Run bot
bot.run(os.getenv('DISCORD_TOKEN'))