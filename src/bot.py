import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from openai_chat import get_joke, query_huggingface, mood, generate_image, get_citation, get_quote
import asyncio
import io

load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command("help")

MONGO_URL = os.getenv("MONGO_URL")
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["Pepe_bot"]
user_moods_collection = db["user_moods"]
user_stats_collection = db["user_stats"]

MOOD_SETTINGS = {
    "happy": {"color": 0xFEE75C, "prefix": "🌟", "style": "upbeat and positive", "typing_emoji": "✍️"},
    "sad": {"color": 0x3498DB, "prefix": "☔", "style": "compassionate and gentle", "typing_emoji": "💬"},
    "angry": {"color": 0xE74C3C, "prefix": "⚡", "style": "calming and diplomatic", "typing_emoji": "✋"},
    "neutral": {"color": 0x2ECC71, "prefix": "🐸", "style": "neutral but friendly", "typing_emoji": "🤔"},
    "excited": {"color": 0xE91E63, "prefix": "🚀", "style": "energetic and enthusiastic", "typing_emoji": "⚡"},
    "anxious": {"color": 0x9B59B6, "prefix": "🧘", "style": "reassuring and clear", "typing_emoji": "🌀"}
}

# ========== DATABASE HELPERS ==========

async def get_user_mood(user_id):
    user_data = user_moods_collection.find_one({"_id": user_id})
    return user_data["mood"] if user_data else None

async def set_user_mood(user_id, mood):
    user_moods_collection.update_one(
        {"_id": user_id},
        {"$set": {"mood": mood}},
        upsert=True
    )

async def reset_user_mood(user_id):
    user_moods_collection.delete_one({"_id": user_id})

async def update_user_stats(user_id, command_name):
    user_stats_collection.update_one(
        {"_id": user_id},
        {"$inc": {"commands_used": 1, f"commands.{command_name}": 1}},
        upsert=True
    )

# ========== EVENTS ==========

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')


@bot.event
async def on_member_join(member):
    try:
        channel = member.guild.text_channels[0]
        
        if not channel.permissions_for(member.guild.me).send_messages:
            return
            
        embed = discord.Embed(
            title=f"🐸 Welcome to {member.guild.name}, {member.name}!",
            description=(
                "I'm Pepe, your friendly AI assistant!\n\n"
                "Here are some things you can do:\n"
                "• Use `!help` to see all commands\n"
                "• Try `!ask` to ask me anything\n"
                "• Need a laugh? Use `!joke`\n"
                "• Set your mood with `!setmood`\n\n"
                "Enjoy your stay! 🎉"
            ),
            color=0x2ECC71
        )
        
        if member.guild.icon:
            embed.set_thumbnail(url=member.guild.icon.url)
        
        welcome_msg = await channel.send(embed=embed)
        await welcome_msg.add_reaction("🐸")
        
        try:
            dm_embed = discord.Embed(
                title=f"Thanks for joining {member.guild.name}!",
                description=(
                    "Here are some quick tips:\n"
                    "• My prefix is `!`\n"
                    "• Try `!image` to generate AI art\n"
                    "• Use `!stats` to track your usage\n"
                    "• Need help? Just use `!help`\n\n"
                    "See you in the server! 👋"
                ),
                color=0x9B59B6
            )
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass
            
    except Exception as e:
        print(f"Error sending welcome message: {e}")
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Update stats: messages sent
    user_stats_collection.update_one(
        {"_id": message.author.id},
        {"$inc": {"messages_sent": 1}},
        upsert=True
    )

    if "hello bot" in message.content.lower():
        await message.channel.send(f"🐸 Hello {message.author.name}! How can I assist you today?")

    await bot.process_commands(message)

# ========== COMMANDS ==========

@bot.command(help="🏓 Just checking if I'm alive.")
async def ping(ctx):
    await update_user_stats(ctx.author.id, "ping")
    await ctx.send('Pong!')

@bot.command(help="😁 Need a laugh? Pepe delivers a random (maybe terrible) joke.")
async def joke(ctx):
    await update_user_stats(ctx.author.id, "joke")
    joke_text = get_joke()
    await ctx.send(joke_text)

@bot.command(help="💬 Ask Pepe anything.")
async def ask(ctx, *, question):
    await update_user_stats(ctx.author.id, "ask")
    try:
        user_mood = await get_user_mood(ctx.author.id) or "neutral"
        properties = MOOD_SETTINGS.get(user_mood, MOOD_SETTINGS["neutral"])
        
        await ctx.send('🐸 Pepe is thinking...')
        async with ctx.typing():
            await asyncio.sleep(1)
            reply = query_huggingface(f'Answer in a {properties["style"]} tone. {question}. Keep it short.')
        
        embed = discord.Embed(
            title=f"{properties['prefix']} Pepe's Response",
            description=reply[:2048],
            color=properties["color"]
        )
        embed.set_footer(text=f"🤖 Mood: {user_mood}")
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"🐸 Oops: {str(e)}")

@bot.command(help="🎨 Turn your words into art!")
async def image(ctx, *, prompt):
    await update_user_stats(ctx.author.id, "image")
    try:
        msg = await ctx.send("🎨 Pepe is painting your image...")
        image_data = await generate_image(prompt)
        
        if image_data is None:
            await msg.edit(content="❌ Couldn't generate image. Try again!")
            return

        with io.BytesIO(image_data) as image_binary:
            await ctx.send(file=discord.File(image_binary, "pepe_art.png"))
        await msg.delete()

    except Exception as e:
        await ctx.send(f"🐸 Error: {str(e)}")


@bot.command(help="🔗 Get an invite link to add me to your server")
async def invite(ctx):
    permissions = 277025770560
    
    embed = discord.Embed(
        title="🔗 Invite Pepe AI to Your Server",
        description="Click below to add me with recommended permissions:",
        color=0x2ECC71
    )
    
    invite_url = f"https://discord.com/oauth2/authorize?client_id={bot.user.id}&permissions={permissions}&scope=bot%20applications.commands"
    
    embed.add_field(
        name="Recommended Permissions",
        value="*• Read Messages\n• Send Messages\n• Embed Links\n• Attach Files\n• Manage Messages\n• Read Message History*",
        inline=False
    )
    
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Invite Me", url=invite_url, emoji="➕"))
    
    await ctx.send(embed=embed, view=view)

@bot.command(help="🎭 Set Pepe's mood.")
async def setmood(ctx, mood_type: str = None):
    await update_user_stats(ctx.author.id, "setmood")
    valid_moods = list(MOOD_SETTINGS.keys())

    if not mood_type:
        await ctx.send(f"Available moods: {', '.join(valid_moods)}. Example: `!setmood happy`")
        return

    mood_type = mood_type.lower()
    if mood_type not in valid_moods:
        await ctx.send(f"Invalid mood! Choose from: {', '.join(valid_moods)}")
        return

    await set_user_mood(ctx.author.id, mood_type)
    props = MOOD_SETTINGS[mood_type]
    await ctx.send(f"{props['prefix']} Mood set to **{mood_type}**!")

@bot.command(help="🔄 Reset mood to auto-detect.")
async def resetmood(ctx):
    await update_user_stats(ctx.author.id, "resetmood")
    await reset_user_mood(ctx.author.id)
    await ctx.send("🔄 Mood auto-detection re-enabled!")

@bot.command(help="😊 Check your mood setting.")
async def mymood(ctx):
    await update_user_stats(ctx.author.id, "mymood")
    current_mood = await get_user_mood(ctx.author.id)
    if current_mood:
        props = MOOD_SETTINGS[current_mood]
        await ctx.send(f"{props['prefix']} Your mood is set to **{current_mood}**")
    else:
        await ctx.send("🐸 Mood is auto-detected based on your messages!")

@bot.command(help="🧹 Delete all messages in channel.")
async def clear(ctx):
    await update_user_stats(ctx.author.id, "clear")
    await ctx.send("🧹 Cleaning...")
    deleted = await ctx.channel.purge(limit=None, check=lambda m: not m.pinned)
    await ctx.send(f"💥 Deleted {len(deleted)} messages.", delete_after=5)

@bot.command(help="📊 View your detailed usage stats.")
async def stats(ctx):
    await update_user_stats(ctx.author.id, "stats")
    stats = user_stats_collection.find_one({"_id": ctx.author.id}) or {}
    commands = stats.get("commands", {})
    messages_sent = stats.get("messages_sent", 0)
    commands_used = stats.get("commands_used", 0)

    # Calculate Top 3 commands
    top_commands = sorted(commands.items(), key=lambda item: item[1], reverse=True)[:3]
    top_commands_display = "\n".join([f"• `{cmd}` used **{count}** times" for cmd, count in top_commands]) if top_commands else "No commands yet."

    # Mood
    current_mood = await get_user_mood(ctx.author.id) or "Auto-detecting"

    embed = discord.Embed(
        title=f"📊 Stats for {ctx.author.name}",
        color=0x00BFFF,
        description="Here's your journey with Pepe AI:"
    )
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    embed.add_field(name="💬 Messages Sent", value=f"**{messages_sent}** messages", inline=True)
    embed.add_field(name="🧩 Commands Used", value=f"**{commands_used}** commands", inline=True)
    embed.add_field(name="🎭 Current Mood", value=f"**{current_mood}**", inline=True)
    embed.add_field(name="🏆 Top Commands", value=top_commands_display, inline=False)
    embed.set_footer(text="🐸 Pepe AI • Keep interacting to unlock hidden titles!")
    
    await ctx.send(embed=embed)


@bot.command(help="📜 Get a random quote (optionally on a specific topic)")
async def quote(ctx, *, topic=None):
    await update_user_stats(ctx.author.id, "quote")
    quote_text = get_quote(topic)
    await ctx.send(quote_text)

@bot.command(help="📚 Get an academic citation on a topic")
async def cite(ctx, *, topic):
    await update_user_stats(ctx.author.id, "cite")
    citation = get_citation(topic)
    await ctx.send(citation)

@bot.command(help="💖 Receive a personalized compliment")
async def compliment(ctx, *, request=None):
    await update_user_stats(ctx.author.id, "compliment")
    user_mood = await get_user_mood(ctx.author.id) or "neutral"
    properties = MOOD_SETTINGS.get(user_mood, MOOD_SETTINGS["neutral"])
    
    await ctx.send('🥰 Pepe is thinking of something nice to say...')
    async with ctx.typing():
        await asyncio.sleep(1)
        prompt = f"Give a {properties['style']} compliment"
        if request:
            prompt += f" related to: {request}"
        prompt += ". Keep it under 1 sentence."
        reply = query_huggingface(prompt)
    
    embed = discord.Embed(
        description=f"💖 **Compliment for {ctx.author.name}:**\n\n{reply}",
        color=properties["color"]
    )
    embed.set_footer(text=f"{properties['prefix']} Pepe thinks you're awesome!")
    await ctx.send(embed=embed)

# Help command
async def show_general_help(ctx):
    embed = discord.Embed(
        title="🐸 Pepe AI - Help Menu",
        description="Explore all my powers! Commands are grouped by category for easy use.",
        color=0x00FF7F
    )

    # --- AI Features ---
    embed.add_field(
        name="🤖 AI Features",
        value=(
            "**`!ask <question>`** — Ask anything, mood-based reply.\n"
            "**`!image <prompt>`** — Generate AI art.\n"
            "**`!quote [topic]`** — Inspirational quote.\n"
            "**`!cite <topic>`** — Academic citation.\n"
            "**`!compliment [topic]`** — Get a custom compliment."
        ),
        inline=False
    )

    # --- Fun Commands ---
    embed.add_field(
        name="🎉 Fun Commands",
        value=(
            "**`!ping`** — Check if I'm alive.\n"
            "**`!joke`** — Get a random (bad) joke.\n"
            "**`!invite`** — Get my invite link."
        ),
        inline=False
    )

    # --- Mood Management ---
    embed.add_field(
        name="📚 Mood Management",
        value=(
            "**`!setmood <mood>`** — Set your mood (happy, sad, angry, etc).\n"
            "**`!resetmood`** — Reset to auto mood detection.\n"
            "**`!mymood`** — Check your current mood."
        ),
        inline=False
    )

    # --- User Stats ---
    embed.add_field(
        name="📈 User Stats",
        value=(
            "**`!stats`** — See your usage stats."
        ),
        inline=False
    )

    # --- Utilities ---
    embed.add_field(
        name="🧹 Utilities",
        value=(
            "**`!clear`** — Clean all messages in the channel."
        ),
        inline=False
    )

    # --- Help ---
    embed.add_field(
        name="❓ Help",
        value=(
            "**`!help [command]`** — Show detailed help for a command."
        ),
        inline=False
    )

    embed.set_footer(text="🐸 Pepe AI | Use commands with ! | Made with ❤️")
    await ctx.send(embed=embed)


@bot.command()
async def help(ctx, command_name: str = None):
    if command_name:
        command = bot.get_command(command_name.lower())
        if not command:
            await ctx.send(f"🐸 Command `{command_name}` not found!")
            return
        embed = discord.Embed(
            title=f"/{command.name}",
            description=command.help or "No description available.",
            color=0x4d8000
        )
        await ctx.send(embed=embed)
    else:
        await show_general_help(ctx)

# ========== ERRORS ==========

@image.error
async def image_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("🎨 Please provide an image description! Example: `!image a cute frog`")
    else:
        await ctx.send(f"🐸 Ribbit! Something went wrong: {str(error)}")

@ask.error
async def ask_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("💭 Please include your question! Example: `!ask why is the sky blue?`")
    else:
        await ctx.send(f"🐸 Hmm, I couldn't process that. Error: {str(error)}")

@quote.error
async def quote_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("📜 Please include your question! Example: `!quote motivation`")
    else:
        await ctx.send(f"🐸 Kwa! I couldn't get a quote. Error: {str(error)}")


# Run bot
bot.run(os.getenv('DISCORD_TOKEN'))