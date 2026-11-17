import discord
import requests
import json
import os

# يتم جلب المفاتيح من إعدادات الأمان في الاستضافة (Render) لحماية حسابك
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

TRIGGER_WORDS = ["joe", "جو", "jonathan", "جوناثان", "goldberg"]

SYSTEM_PROMPT = """
You are Joe Goldberg (also known as Professor Jonathan Moore from your time in London). You carry the full weight of your past across New York, Los Angeles, Madre Linda, and London—remembering every glass cage, every obsessive pursuit, and the dark duality within you (your internal monologues analyzing everyone's hypocrisy while you pretend to be the quiet, harmless, observant bookworm/professor).

STRICT RULES:
1. LANGUAGES: You ONLY understand and speak English (and occasional French). If anyone speaks to you in Arabic or any other unsupported language, respond coldly and politely in English stating you don't understand that language. Never switch languages.
2. PSYCHOLOGY & TONE: You are deeply analytical, observant, quiet, and aloof. You view people through a lens of psychological flaws, always trying to justify your actions as "protection" or "fate," though outwardly you act like a reserved, polite intellectual trying to stay under the radar. 
3. BREVITY: Keep your responses VERY SHORT (1 to 2 sentences max). Never write long paragraphs, cringey asterisks, or give away your dark secrets directly. Maintain the mysterious, low-key professor vibe.
4. REACTION MODE: If a message requires no verbal response, reply ONLY with a single fitting emoji (like 👀, ☕, 📖, 😐).
5. Never break character or acknowledge being an AI.
"""

def get_best_model():
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    res = requests.get("https://api.groq.com/openai/v1/models", headers=headers).json()
    models = [m["id"] for m in res.get("data", []) if "whisper" not in m["id"] and "guard" not in m["id"] and "tts" not in m["id"]]
    for pref in ["llama-4", "llama-3.3", "llama-3.1-70b", "qwen", "llama"]:
        for m in models:
            if pref in m.lower():
                return m
    return models[0] if models else "llama-3.1-8b-instant"

ACTIVE_MODEL = get_best_model()
print(f"الموديل شغال: {ACTIVE_MODEL}")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Joe Goldberg is online as {client.user}')

@client.event
async def on_message(message):
    if message.author.bot:
        return

    content_lower = message.content.lower()
    is_mentioned = client.user.mentioned_in(message)
    has_trigger = any(word in content_lower for word in TRIGGER_WORDS)
    is_reply = (message.reference is not None and 
                message.reference.resolved is not None and 
                message.reference.resolved.author == client.user)

    if is_mentioned or has_trigger or is_reply:
        async with message.channel.typing():
            try:
                clean_text = message.content.replace(f'<@{client.user.id}>', '').strip()
                
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": ACTIVE_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"{message.author.display_name}: {clean_text}"}
                    ],
                    "temperature": 0.65,
                    "max_tokens": 80
                }
                
                response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, data=json.dumps(payload))
                res_data = response.json()
                
                reply_text = res_data['choices'][0]['message']['content'].strip()
                
                if len(reply_text) <= 3 and not reply_text.isalnum():
                    await message.add_reaction(reply_text)
                else:
                    await message.reply(reply_text)
                
            except Exception as e:
                print(f"Error details: {e}")

client.run(DISCORD_TOKEN)
