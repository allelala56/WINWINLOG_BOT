from fastapi import FastAPI, Request
import httpx, os
from datetime import datetime

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
SOLANA_WALLET = os.getenv("SOLANA_WALLET")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
EURO_TO_SOL = 0.0082

WELCOME_MSG = '''
Bienvenue sur *Black DJ Log* !
Voici nos services disponibles :

- Compte Netflix, Amazon, Facebook, SFR : *15€*
- Technique Prickstell : *50€*
- SIM SFR/ORANGE : *20€*
- Compte Natixis (15 000€) : *300€*
- Recherche de log personnalisé : *25€ les 1200 logs*

Choisis une option ci-dessous :
'''

BUTTONS = [
    [{"text": "Acheter un Compte (15€)", "callback_data": "buy_account"}],
    [{"text": "Technique Prickstell (50€)", "callback_data": "buy_prickstell"}],
    [{"text": "SIM SFR / ORANGE (20€)", "callback_data": "buy_sim_orange"}],
    [{"text": "Compte Natixis (300€)", "callback_data": "buy_natixis"}],
    [{"text": "Log personnalisé 1200 (25€)", "callback_data": "buy_log_custom"}],
]

@app.get("/")
def read_root():
    return {"message": "Bot is running."}

@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()

    if "message" in data and data["message"].get("text") == "/start":
        chat_id = data["message"]["chat"]["id"]
        await send_message(chat_id, WELCOME_MSG, reply_markup={"inline_keyboard": BUTTONS})

    elif "message" in data and data["message"].get("text") == "/admin":
        user_id = data["message"]["from"]["id"]
        if user_id != ADMIN_ID:
            await send_message(user_id, "Accès refusé.")
        else:
            tx_list = await get_recent_payments()
            await send_message(user_id, tx_list)

    elif "callback_query" in data:
        chat_id = data["callback_query"]["message"]["chat"]["id"]
        data_text = data["callback_query"]["data"]

        items = {
            "buy_account": ("Compte", 15),
            "buy_prickstell": ("Prickstell", 50),
            "buy_sim_orange": ("SIM SFR / ORANGE", 20),
            "buy_natixis": ("Compte Natixis (15 000€)", 300),
            "buy_log_custom": ("Log personnalisé (1200)", 25),
        }

        if data_text in items:
            item_name, price = items[data_text]
            msg = await get_payment_instruction(item_name, price)
            await send_message(chat_id, msg)

    return {"ok": True}

async def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    async with httpx.AsyncClient() as client:
        await client.post(f"{API_URL}/sendMessage", json=payload)

async def get_payment_instruction(item: str, price_eur: int):
    price_sol = round(price_eur * EURO_TO_SOL, 4)
    return f'''
Pour acheter *{item}* :

1. Envoie *{price_sol} SOL* à l'adresse suivante :
`{SOLANA_WALLET}`

2. Ajoute un memo : `{item}`

Une fois le paiement reçu, tu recevras un message de confirmation ici.
'''

async def get_recent_payments():
    url = f"https://mainnet.helius.xyz/v0/addresses/{SOLANA_WALLET}/transactions?api-key={HELIUS_API_KEY}&limit=10"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        data = r.json()

    lines = []
    for tx in data:
        if tx.get("type") == "TRANSFER":
            time_unix = int(tx["timestamp"])
            dt = datetime.utcfromtimestamp(time_unix).strftime("%Y-%m-%d %H:%M")
            sender = tx["nativeTransfers"][0]["fromUserAccount"]
            sol = float(tx["nativeTransfers"][0]["amount"]) / 1e9
            memo = tx.get("memo", "Aucun")

            lines.append(f"• {dt}\n→ {sol:.4f} SOL de {sender}\nMémo : {memo}\n")
    return "*Transactions récentes :*\n\n" + "\n".join(lines[:5])
