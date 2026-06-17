import os
import aiohttp
import discord
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# ollama에 요청 후 content return
async def ask_ollama(messages: list[dict]) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.3
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(OLLAMA_URL, json=payload, timeout=120) as response:
            response.raise_for_status()
            data = await response.json()
            return data["message"]["content"]
        
# 최근 채팅 10개 가져오는 함수
async def get_recent_channel_messages(message: discord.Message, limit: int = 10) -> list[dict]:
    recent_messages = []
    
    async for msg in message.channel.history(limit=limit + 1):
        # 현재 봇을 호출한 메세지는 마지막아 따로 추가할거라 제외
        if msg.id == message.id:
            continue
        
        # 내용 없는 메세지 패스
        if not msg.content.strip():
            continue
        
        # 봇 메세지와 일반 사용자 메세지 role 구분
        role = "assistant" if msg.author == client.user else "user"
        
        content = f"{msg.author.display_name}: {msg.content}"
        
        recent_messages.append({
            "role":role,
            "content":content
        })
        
        if len(recent_messages) >= limit:
            break
    
    # channel.history는 최근 메세지부터 가져오르모 리버스를 통해 시간순으로 정렬
    recent_messages.reverse()
    
    return recent_messages


@client.event
async def on_ready():
    print(f"봇 로그인 완료: {client.user}")


@client.event
async def on_message(message: discord.Message):
    # 봇 자신의 메시지는 무시
    if message.author.bot:
        return

    # 봇이 멘션된 경우에만 반응
    if client.user not in message.mentions:
        return

    # 메시지에서 봇 멘션 부분 제거
    user_prompt = message.content.replace(f"<@{client.user.id}>", "").strip()
    user_prompt = user_prompt.replace(f"<@!{client.user.id}>", "").strip()
    
    if not user_prompt:
        await message.reply("질문을 같이 입력해줘.")
        return

    async with message.channel.typing():
        try:
            # 현재 메세지 + 이전 기록 10개 합쳐서 제출
            recent_messages = await get_recent_channel_messages(message, limit=10)
            
            messages = [
                {
                    "role": "system",
                    "content": (
                        "너는 한국어 전용 Discord AI 봇이다. "
                        "모든 답변은 반드시 한국어로만 작성한다. "
                        "중국어, 일본어, 영어 문장을 절대 섞지 않는다. "
                        "아래에는 현재 채널의 최근 대화가 포함되어 있다. "
                        "최근 대화를 참고해서 문맥에 맞게 답변하되, 마지막 사용자 요청에 답변하라."
                    )
                },
                *recent_messages,
                {
                    "role": "user",
                    "content": f"{message.author.display_name}: {user_prompt}"
                }
            ]
            
            answer = await ask_ollama(messages)
        except Exception as e:
            answer = f"오류가 발생했어: `{e}`"

    # 디스코드 메시지 길이 제한 대응
    if len(answer) > 1900:
        answer = answer[:1900] + "\n\n...답변이 너무 길어서 잘랐어."

    await message.reply(answer)


client.run(DISCORD_TOKEN)