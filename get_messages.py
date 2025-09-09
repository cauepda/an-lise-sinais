import csv
import os
from dotenv import load_dotenv
from telethon import TelegramClient

# Carrega variáveis do .env
load_dotenv()
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session_name = os.getenv("SESSION_NAME", "session")

# Cria cliente
client = TelegramClient(session_name, api_id, api_hash)

async def export_group_messages(group_username, output_file="mensagens.csv", limit=500):
    """
    Exporta mensagens de um grupo para um arquivo CSV.
    
    :param group_username: @username do grupo ou link (ex: 'https://t.me/nome_do_grupo')
    :param output_file: nome do arquivo de saída
    :param limit: limite de mensagens (None para todas)
    """
    # Abre arquivo CSV
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "data", "autor_id", "mensagem"])

        async for message in client.iter_messages(group_username, limit=limit):
            writer.writerow([
                message.id,
                message.date.strftime("%Y-%m-%d %H:%M:%S") if message.date else "",
                message.sender_id,
                message.text if message.text else ""
            ])

    print(f"Exportação concluída! Mensagens salvas em {output_file}")

async def main():
    # Substitua pelo @username ou link do grupo
    grupo = "https://t.me/+bhVaGzRkhuozZDIx"  # ex: "https://t.me/grupoTeste"
    await export_group_messages(grupo, output_file="mensagens.csv", limit=100000)

with client:
    client.loop.run_until_complete(main())