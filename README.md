# 🐸 **Pepe AI Frog 🤖**

**Pepe AI Frog** is a fun and intelligent Discord bot built by an **8th-grade full-stack developer**! It combines humor, AI tools, image generation, emotion detection, and academic citation — all powered by **Python**, **MongoDB**, and **Hugging Face APIs**.

---

## 🌟 **Features**

| Feature | Description |
|--------|-------------|
| 🤣 **Jokes** | Get fun, random dad jokes to brighten your day. |
| 💬 **AI Q&A** | Ask questions and get styled, helpful replies from Mixtral AI. |
| 🧠 **Mood Detection** | Detects user emotion using a DistilRoBERTa-based model. |
| 🎨 **Image Generation** | Generates art from your prompt using Stable Diffusion XL. |
| 📚 **Academic Citations** | Pulls real citations from Crossref for essays, research, or curiosity. |
| ✍️ **Text Summarization** | Summarizes large chunks of text using Mixtral. |
| 🌍 **Translation** | Translates input text using natural AI output. |
| 🌱 **Inspirational Quotes** | Get random or topic-based wisdom. |
| 📊 **User & Server Stats** | Tracks commands, moods, messages, and usage. |

---

## 🧠 **AI Models Used**

- **Mixtral 8x7B Instruct** (Hugging Face) for Q&A, summaries, translations  
- **DistilRoBERTa-base-emotion** by `j-hartmann` for mood detection  
- **Stable Diffusion XL** for image generation  
- **Crossref API** for real academic citations  
- **ZenQuotes API** for motivational quotes  

---

## 🗃️ **MongoDB Tracking System**

All users, moods, and command usages are stored and managed in a **MongoDB** database.

### 📌 **Collections**

- `users` — tracks username, join date, last seen, mood, message count  
- `command_usage` — command frequency, last used time  
- `user_moods` — mood history with timestamps  

### 📊 **Stats Functions**

- **User stats**: message count, top commands, mood history  
- **Server stats**: most active user, top commands, total users/messages  

---

## ⚙️ **Environment Setup**

Create a `.env` file and include the following:

```env
HUGFACE_TOKEN=your_huggingface_token_here  
MONGODB_URI=your_mongodb_uri_here
```

---

## 🚀 **Installation**

1. **Clone the repo:**

    ```bash
    git clone https://github.com/yourname/pepe-ai-frog.git
    cd pepe-ai-frog
    ```

2. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Set up your `.env` file.**

4. **Run the bot:**

    ```bash
    python main.py
    ```

---

## 🧪 **Sample Commands**

```python
get_joke()
query_huggingface("What is a black hole?")
mood("I feel really anxious today.")
await generate_image("A futuristic frog warrior")
get_citation("quantum computing")
get_quote("perseverance")
summarize_text("This is a long article about...")
translate_text("Hello, how are you?")
```

---

## 📁 **File Structure**

```
pepe-ai-frog/
│
├── main.py              # Main bot logic
├── database.py          # MongoDB user/command/mood tracker
├── .env                 # Tokens and secrets
├── requirements.txt     # Python dependencies
└── README.md            # You're here!
```

---

## ✨ **Made by an 8th Grade Full Stack Developer ❤️**

I'm building this as my passion project.  
**Contributions, feedback, and ideas are always welcome!**
