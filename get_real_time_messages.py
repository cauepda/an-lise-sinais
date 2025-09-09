import os
from dotenv import load_dotenv
from telethon import TelegramClient, events

# Carrega variáveis do .env
load_dotenv()
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session_name = os.getenv("SESSION_NAME", "session")

# Cria cliente
client = TelegramClient(session_name, api_id, api_hash)

# Handler: dispara sempre que uma mensagem nova aparecer no grupo
@client.on(events.NewMessage(chats=["https://t.me/+fP8CwJ_w3ONhOThh", "https://t.me/+bhVaGzRkhuozZDIx"]))
async def handler(event):
    mensagem = event.message.message
    autor_id = event.sender_id
    data = event.message.date

    # Exemplo: imprime na tela
    print(f"[{data}] {autor_id}: {mensagem}")

    # Exemplo: salvar em arquivo de texto
    with open("mensagens_realtime.txt", "a", encoding="utf-8") as f:
        f.write(f"[{data}] {autor_id}: {mensagem}\n")

# Inicia o cliente (fica escutando em loop)
print("Escutando mensagens em tempo real...")
client.start()
client.run_until_disconnected()