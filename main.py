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
✨ *Bienvenue chez SPYDER & JAME* ✨

Spécialistes du *DUMB*, du *LOG ciblé*, et de la *recherche sur-mesure* 🤖🔎

Voici nos services disponibles :

✅ *Compte Netflix, Amazon, Facebook, SFR* : 15€
⚖️ *Technique Prickstell* (sortie des prickstell) : 50€
🚗 *SIM SFR/ORANGE* : 20€
📶 *SIM PRIXTEL* : 10€
💵 *Compte Natixis (15 000€)* : 300€
🤮 *Recherche de log personnalisée (1200 logs)* : 25€
🌐 *Booking -50%* : sur demande privée 
📧 *Mailing List ciblée* : 20€ en SOL
📇 *Num List ciblée* : 7€ en SOL

*Choisis ton offre ci-dessous ou contacte @blackdjdj en privé pour personnalisation.*
'''

AIDE_MSG = '''
🆘 *AIDE - Comment acheter ?*

1. Clique sur un bouton ci-dessous
2. Envoie le montant en SOL à l'adresse donnée
3. Mets le *nom du produit en memo*
4. Dès réception → tu reçois ton accès ou on te contacte

💬 Pour toute question ou personnalisation, contacte @BlackDJ
'''

BUTTONS = [
    [{"text": "Acheter un Compte (15€)", "callback_data": "buy_account"}],
    [{"text": "Technique Prickstell (50€)", "callback_data": "buy_prickstell"}],
    [{"text": "SIM SFR / ORANGE (20€)", "callback_data": "buy_sim_orange"}],
    [{"text": "SIM PRIXTEL (10€)", "callback_data": "buy_sim_prixtel"}],
    [{"text": "Compte Natixis (300€)", "callback_data": "buy_natixis"}],
    [{"text": "Log personnalisé 1200 (25€)", "callback_data": "buy_log_custom"}],
    [{"text": "Booking -50% (contact)", "callback_data": "buy_booking"}],
    [{"text": "Mailing List ciblée (20€)", "callback_data": "buy_ml"}],
    [{"text": "Num List ciblée (7€)", "callback_data": "buy_nl"}],
    [{"text": "📩 Contacter le support", "url": "https://t.me/blackdjdj"}],
]

@app.get("/")
def read_root():
    return {"message": "Bot is running."}

@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()

    if "message" in data:
        text = data["message"].get("text", "")
        chat_id = data["message"]["chat"]["id"]
        user_id = data["message"]["from"]["id"]

        if text == "/start":
            await send_message(chat_id, WELCOME_MSG, reply_markup={"inline_keyboard": BUTTONS})

        elif text == "/admin":
            if user_id != ADMIN_ID:
                await send_message(user_id, "Accès refusé.")
            else:
                tx_list = await get_recent_payments()
                await send_message(user_id, tx_list)

        elif text == "/aide":
            await send_message(chat_id, AIDE_MSG)

        await send_message(chat_id, WELCOME_MSG, reply_markup={"inline_keyboard": BUTTONS})

    elif "callback_query" in data:
        chat_id = data["callback_query"]["message"]["chat"]["id"]
        data_text = data["callback_query"]["data"]

        items = {
            "buy_account": ("Compte", 15),
            "buy_prickstell": ("Prickstell", 50),
            "buy_sim_orange": ("SIM SFR / ORANGE", 20),
            "buy_sim_prixtel": ("SIM PRIXTEL", 10),
            "buy_natixis": ("Compte Natixis (15 000€)", 300),
            "buy_log_custom": ("Log personnalisé (1200)", 25),
            "buy_ml": ("Mailing List ciblée", 20),
            "buy_nl": ("Num List ciblée", 7),
        }

        if data_text == "buy_booking":
            await send_message(chat_id, "🏨 Pour l'offre *Booking -50%*, merci de nous envoyer en privé :\n\n- Le lien de l'annonce\n- Les dates souhaitées\n- Nombre de nuits et personnes")
        elif data_text in items:
            item_name, price = items[data_text]
            msg = await get_payment_instruction(item_name, price)
            await send_message(chat_id, msg)
        await send_message(chat_id, WELCOME_MSG, reply_markup={"inline_keyboard": BUTTONS})

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
