# 클래스로 worker 관리

import asyncio
import discord

from config import QUEUE_MAX_SIZE, HISTORY_USE_LIMIT
from services.ollama import ask_ollama
from utils.message import split_message
from bot.history import ChannelHistoryManager

class RequestQueueManager:
    def __init__(self, client: discord.Client, history_manager: ChannelHistoryManager):
        self.client = client
        self.history_manager = history_manager
        
        self.queue = asyncio.Queue(maxsize=QUEUE_MAX_SIZE)
        self.worker_task = None
        self.is_processing = False
    
    # worker 실행    
    def start_worker(self):
        if self.worker_task is None or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._worker())
            print("요청 큐 worker 시작")
    
    # 요청 추가
    async def enqueue(self, message: discord.Message, user_prompt: str):
        if self.queue.full():
            await message.reply("현재 요청이 너무 많이 밀려 있어. 잠시 후 다시 요청해줘.")
            return

        if self.is_processing:
            await self.queue.put((message, user_prompt))
            await message.reply(
                f"요청을 대기열에 추가했어. 현재 대기 순번: {self.queue.qsize()}번"
            )
        else:
            await self.queue.put((message, user_prompt))
    
    # AI 요청 후 답장      
    async def _worker(self):
        while True:
            message, user_prompt = await self.queue.get()
            self.is_processing = True

            try:
                answer = await self._process_request(message, user_prompt)

                for chunk in split_message(answer):
                    await message.reply(chunk)

            finally:
                self.queue.task_done()

                if self.queue.empty():
                    self.is_processing = False
                    
    # AI에게 프롬프트와 함께 질문
    async def _process_request(self, message: discord.Message, user_prompt: str) -> str:
        try:
            async with message.channel.typing():
                recent_messages = await self.history_manager.get_recent_messages(
                    message=message,
                    client_user=self.client.user,
                    limit=HISTORY_USE_LIMIT
                )

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

                return await ask_ollama(messages)

        except Exception as e:
            return f"오류가 발생했어: `{e}`"
    