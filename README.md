
# Black DJ Bot – Telegram Bot avec Paiement Solana

Bot Telegram pour vendre comptes et services, avec paiement en $SOL.

## Installation rapide

### 1. Clone le repo

```bash
git clone https://github.com/ton-url/blackdjbot-solana.git
cd blackdjbot-solana
```

### 2. Configure ton `.env`

Copie `.env.example` et remplis :

- Ton token Telegram
- Ton URL Render
- Adresse SOL
- Clé Helius
- Ton ID Telegram admin

### 3. Déploie sur Render

- Crée un service Web
- Ajoute toutes les variables d’environnement
- Déploie
- Lance `setWebhook` sur Telegram

```bash
curl https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://TON_RENDER_URL/webhook
```

### 4. Commandes disponibles

- `/start` : accueil + menu d'achat
- `/admin` : voir paiements reçus

---
Made with love for Black DJ Log
