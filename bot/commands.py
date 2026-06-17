import discord
from bot.history import ChannelHistoryManager


HELP_TEXT = (
    "--사용 가능한 명령어--\n"
    "`@준평냥 질문내용` - AI에게 질문하기\n"
    "`@준평냥 초기화` - AI 채널별 문맥 초기화\n"
    "`@준평냥 도움말` - 명령어 목록 보기"
)

# 메시지 앞의 @ 제거
def remove_bot_mention(message: discord.Message, bot_user: discord.ClientUser) -> str:
    content = message.content

    content = content.replace(f"<@{bot_user.id}>", "")
    content = content.replace(f"<@!{bot_user.id}>", "")

    return content.strip()

# 명령어 처리가 됐으면 True 반환, 아니면 False 반환 ( False일시 AI 질문임 )
async def handle_command(
    message: discord.Message,
    user_prompt: str,
    history_manager: ChannelHistoryManager
) -> bool:

    if user_prompt.lower() in ["도움말", "help", "명령어", "사용법"]:
        await message.reply(HELP_TEXT)
        return True

    if user_prompt == "초기화":
        history_manager.reset_channel(message)
        await message.reply("이 채널의 대화 문맥이 초기화됐어. 이제 이전 채팅은 참고하지 않을게.")
        return True

    if not user_prompt:
        await message.reply("질문을 같이 입력해줘.")
        return True

    return False