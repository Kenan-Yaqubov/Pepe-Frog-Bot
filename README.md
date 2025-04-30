🐸 Pepe AI - Discord Bot
Welcome to Pepe AI, your friendly and hilarious Discord bot! Whether you're feeling happy, sad, or just need a good laugh, Pepe has got you covered with personalized responses, fun commands, and even art generation. Let's dive into all the awesome features this little frog can do! 🐸💚

📦 Installation
To get started with Pepe AI, follow these steps:

Clone this repo:

bash
git clone https://github.com/your-repo/pepe-bot.git
cd pepe-bot
Install the dependencies:

bash
pip install -r requirements.txt
Create a .env file in the root directory with your bot's token and MongoDB URL:

env
DISCORD_TOKEN=your-discord-token
MONGO_URL=your-mongo-db-url
Run the bot:

bash
python bot.py
🐸 Commands Overview
Pepe is not just a frog 🐸—he's a multi-talented AI assistant who can make you laugh, paint AI art, give you quotes, and so much more. Here’s what you can do:

🤖 AI Features
!ask <question> — Ask Pepe anything! He'll respond in a mood-based style. (Like a froggy fortune teller 🐸🔮)

!image <prompt> — Generate AI art based on your prompts. "Make me a frog with a crown!" 👑

!quote [topic] — Need some inspiration? Get a random quote. 📜

!cite <topic> — Want to sound smart? Get an academic citation! 🎓

!compliment [topic] — Pepe gives you a personalized compliment! 🥰

🎉 Fun Commands
!ping — Just checking if I’m alive! Ping me! 🏓

!joke — Need a laugh? Pepe’s got the worst jokes! 😂

!invite — Invite Pepe to your server and let the fun begin! 🎉

📚 Mood Management
!setmood <mood> — Set your mood! Feeling happy? Sad? Or maybe angry? 🐸

!resetmood — Reset your mood to auto-detect! 🌈

!mymood — Check your current mood setting! 😊

📈 User Stats
!stats — Check your usage stats. How many times have you summoned Pepe? 📊

🧹 Utilities
!clear — Clean up the channel by deleting all non-pinned messages. ✨

🔧 Configuration
MongoDB Setup
Pepe uses MongoDB to store user data like moods and stats. You need to set up a MongoDB instance and connect it to your bot.

Go to MongoDB Atlas to create a free database.

Add the connection string to the .env file:

env
Копировать
Редактировать
MONGO_URL=your-mongo-db-url
🎨 Pepe's Moods
Pepe has a variety of moods to choose from, each with its own unique vibe:

Happy: 🌟 "I'm feeling awesome!"

Sad: ☔ "I'm a little down, but still here for you!"

Angry: ⚡ "Watch out! Pepe's mad!"

Neutral: 🐸 "Just chilling, no big deal."

Excited: 🚀 "Pepe’s on fire! Let's gooo!"

Anxious: 🧘 "Pepe’s calming down... 🌿"

Set your mood with !setmood <mood> and see the magic happen! ✨

🛠️ Development
Languages Used: Python 🐍

Libraries Used: discord.py, pymongo, openai, dotenv

Database: MongoDB for user stats and moods

API: Hugging Face for AI queries

📜 License
This project is open-source and available under the MIT License. Feel free to fork and make it your own!

🐸 Support & Contributions
Got suggestions? Found a bug? Feel free to open an issue or contribute to the repo.

🎉 Conclusion
Pepe AI is here to make your Discord experience more fun and engaging! From jokes and art to mood-based responses, this little frog will keep you entertained. Hop on and enjoy the ride! 🐸💚