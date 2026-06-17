from config import DISCORD_TOKEN
from bot.client import create_client


def main():
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN이 설정되지 않았어. .env 파일을 확인해줘.")

    client = create_client()
    client.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()