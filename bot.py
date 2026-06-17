import os
import aiohttp
import discord
import asyncio
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

request_queue = asyncio.Queue(maxsize=10)
worker_task = None # 대기열 스케줄링 worker
is_processing = False # 작업 처리중인지 확인하는 변수

channel_reset_times = {} # 채널별 reset time

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
    
    reset_time = channel_reset_times.get(message.channel.id)
    
    async for msg in message.channel.history(limit=50):
        # 현재 봇을 호출한 메세지는 마지막아 따로 추가할거라 제외
        if msg.id == message.id:
            continue
        
        # reset 이전 메세지 패스
        if reset_time is not None and msg.created_at <= reset_time:
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

# 대화 청크로 자르는 함수
def split_message(text: str, max_length: int = 1900) -> list[str]:
    chunks = []

    while len(text) > max_length:
        split_index = text.rfind("\n", 0, max_length)

        if split_index == -1:
            split_index = max_length

        chunks.append(text[:split_index])
        text = text[split_index:].lstrip()

    if text:
        chunks.append(text)

    return chunks

# 요청 큐 스케줄링 worker 함수
async def request_worker():
    global is_processing
    while True:
        message, user_prompt = await request_queue.get()
        
        is_processing = True

        try:
            async with message.channel.typing():
                try:
                    recent_messages = await get_recent_channel_messages(message, limit=10)
                    
                    messages = [
                        {
                            "role": "system",
                            "content": (
                                "너는 한국어 전용 Discord AI 봇이다. "
                                "모든 답변은 반드시 한국어로만 작성한다. "
                                "중국어, 일본어, 영어 문장을 절대 섞지 않는다. "
                                "아래에는 현재 채널의 최근 대화가 포함되어 있다. "
                                "최근 대화는 참고용이며, 반드시 마지막 사용자 요청에 답변하라."
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
                    
            for chunk in split_message(answer):
                await message.reply(chunk)
                
        finally:
            request_queue.task_done()
            
            if request_queue.empty():
                is_processing = False


@client.event
async def on_ready():
    global worker_task
    
    print(f"봇 로그인 완료: {client.user}")
    
    # 중복 worker 생성 방지
    if worker_task is None or worker_task.done():
        worker_task = asyncio.create_task(request_worker())
        print("요청 큐 worker 시작")


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
    
    if user_prompt == "초기화":
        channel_reset_times[message.channel.id] = message.created_at
        await message.reply("이 채널의 대화 문맥이 초기화됐어. 이제 이전 채팅은 참고하지 않을게.")
        return
    
    if not user_prompt:
        await message.reply("질문을 같이 입력해줘.")
        return

    if request_queue.full():
        await message.reply("현재 요청이 너무 많이 밀려 있어. 잠시 후 다시 요청해줘.")
        return
    
    # 대기열 등록
    if is_processing:
        await request_queue.put((message,user_prompt))
        await message.reply(f"요청을 대기열에 추가했어. 현재 대기 순번: {request_queue.qsize()}번")
    else:
        await request_queue.put((message,user_prompt))

client.run(DISCORD_TOKEN)