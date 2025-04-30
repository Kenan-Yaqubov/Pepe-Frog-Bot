import requests
import random
import os
from dotenv import load_dotenv
from transformers import pipeline
import aiohttp
import asyncio
from bs4 import BeautifulSoup
load_dotenv()


def get_joke():
    jokes = [
        "Why did the scarecrow win an award? Because he was outstanding in his field!",
        "Why don’t skeletons fight each other? They don’t have the guts.",
        "What do you call cheese that isn't yours? Nacho cheese!"
    ]
    return random.choice(jokes)


def query_huggingface(prompt: str) -> str:
    """
    Sends a prompt to Hugging Face Inference API using Mixtral.
    Returns a Discord-formatted reply (bold, italic, code).
    """
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
    headers = {"Authorization": f"Bearer {os.getenv('HUGFACE_TOKEN')}"}

    formatted_prompt = (
        f"Answer the following question in a friendly and helpful tone. "
        f"Use Discord formatting: **bold**, *italic*, and code blocks (```). "
        f"Keep the answer under 512 characters.\n\n"
        f"Question: {prompt}"
    )

    data = {
        "inputs": f"<s>[INST] {formatted_prompt} [/INST]",
        "parameters": {
            "temperature": 0.7,
            "max_new_tokens": 512,
            "top_p": 0.9
        }
    }

    response = requests.post(API_URL, headers=headers, json=data)
    result = response.json()

    try:
        reply = result[0]["generated_text"].replace(formatted_prompt, "").strip()
        reply = reply.replace("<s>[INST]", "").replace("[/INST]", "").strip()
        return reply
    except Exception as e:
        print(f"Error parsing response: {e}")
        return "Oops! Couldn't parse the response properly."


emotion_class = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")


def mood(text: str) -> str:
    """Detects mood from text only (no ctx dependency)."""
    if len(text) < 5:
        return "neutral"

    try:
        emotion = emotion_class(text)
        label = emotion[0]['label'].lower()
        mood_mapping = {
            'anger': 'angry',
            'disgust': 'angry',
            'fear': 'anxious',
            'joy': 'happy',
            'neutral': 'neutral',
            'sadness': 'sad',
            'surprise': 'excited'
        }
        return mood_mapping.get(label, 'neutral')
    except Exception as e:
        print(f"Error detecting mood: {e}")
        return "neutral"



async def generate_image(prompt: str):
    """Generate an image using Stable Diffusion"""
    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {os.getenv('HUGFACE_TOKEN')}"}
    json_data = {"inputs": prompt}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=json_data) as resp:
                if resp.status == 200:
                    return await resp.read()
                elif resp.status == 503:
                    error = await resp.json()
                    estimated_time = error.get("estimated_time", 30)
                    print(f"Model is loading, waiting {estimated_time} seconds")
                    await asyncio.sleep(estimated_time)
                    return await generate_image(prompt) 
                else:
                    error = await resp.json()
                    print(f"Generation failed: {error}")
                    return None
    except Exception as e:
        print(f"Error in generate_image: {str(e)}")
        return None


def get_citation(topic: str) -> str:
    """Fetches academic citations from Crossref"""
    try:
        url = f"https://api.crossref.org/works?query={topic.replace(' ', '+')}&rows=3"
        headers = {'User-Agent': 'YourBot/1.0 (mail@example.com)'}  # Required
        
        response = requests.get(url, headers=headers)
        data = response.json()
        
        citations = []
        for item in data['message']['items']:
            title = item.get('title', ['Untitled'])[0]
            doi = item.get('DOI', 'No DOI')
            link = f"https://doi.org/{doi}"
            citations.append(f"**{title}**\n{link}")
            
        return "\n\n".join(citations) if citations else "No citations found"
    except Exception as e:
        return f"⚠️ Error fetching citations: {str(e)}"


def get_quote(topic: str = None) -> str:
    """Fetches a random quote (or topic-based if supported)"""
    try:
        url = "https://api.quotable.io/random"
        if topic:
            url += f"?tags={topic.lower().replace(' ', '-')}"
        
        response = requests.get(url)
        data = response.json()
        
        return f'"{data["content"]}" — {data["author"]}'
    except Exception as e:
        return f"⚠️ Error fetching quote: {str(e)}"