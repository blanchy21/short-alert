# Short Alert

Hourly moon-dump short alerts for Hyperliquid, sent to Telegram. Paper mode only — it never places orders.

- `moon_dump_monitor.py` — your scanner, unchanged. Its scoring is what decides the score.
- `short_alert.py` — runs the scan and adds the Short Seller rules:
  - score 55+, not in the Day 2 bounce zone
  - rolled over = peak at least 1h ago and price at least 1% below it
  - no new shorts while BTC is above a rising 4h EMA21
  - stop 1.5× ATR (max 10%), TP1 at nearest strong support (else 2× ATR)
  - one alert per coin per day, 24h max hold, paper day-stop at −$11.60
- `state/state.json` — the paper-trade log (open, closed, near-misses). Committed back after each run.
- Daily tally to Telegram at 21:00 Dublin.

## Setup (about 10 minutes)

### 1. Telegram bot
1. In Telegram, message **@BotFather** → `/newbot` → pick a name. Copy the **token** it gives you.
2. Send any message (e.g. "hi") to your new bot.
3. Open `https://api.telegram.org/bot<TOKEN>/getUpdates` in a browser and copy the number after `"chat":{"id":` — that's your **chat ID**.

(If you still have the token and chat ID from the old Telegram setup, use those instead.)

### 2. GitHub repo
1. Create a new **private** repo on GitHub, e.g. `short-alert`.
2. Upload everything in this folder, including the hidden `.github` folder and `state/`.
   Easiest: `git init && git add . && git commit -m init && git remote add origin <repo-url> && git push -u origin main`
3. Repo → **Settings → Secrets and variables → Actions → New repository secret**:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. Repo → **Actions** tab → enable workflows if asked → **short-alert → Run workflow** to test.
   The log shows every mooner scored and why it was or wasn't alerted.

After that it runs every hour by itself. An hourly run uses roughly 720 of the 2,000 free Actions minutes a month on a private repo.

### 3. Turn off the Grokbot hourly runs
Once Telegram alerts are coming through, stop Short Seller's hourly paper runs on Grokbot so you're not paying for both.

## Changing the rules
All thresholds are at the top of `short_alert.py` (`MIN_SCORE`, `MAX_STOP_PCT`, `BTC_EMA_PERIOD`, etc.).
