# Short Alert

Hourly moon-dump short alerts for Hyperliquid, sent to Telegram. Paper mode by default; live mode places real shorts with exchange-side stops (see "Paper / live switch").

- `moon_dump_monitor.py` — your scanner, unchanged. Its scoring is what decides the score.
- `short_alert.py` — runs the scan and adds the Short Seller rules:
  - score 55+, not in the Day 2 bounce zone
  - rolled over = peak at least 1h ago and price at least 1% below it
  - no new shorts while BTC is above a rising 4h EMA21
  - stop 1.5× ATR (max 10%), TP1 at nearest strong support (else 2× ATR)
  - one alert per coin per day, 24h max hold, TP1 no further than −20%
  - sizing and caps matched to Grokbot's Short Seller (see below)
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

After that it runs every 30 minutes (see step 4).

### 3. Turn off the Grokbot hourly runs
Once Telegram alerts are coming through, stop Short Seller's hourly paper runs on Grokbot so you're not paying for both.

### 4. Reliable hourly trigger (cron-job.org)
GitHub's own schedule is "best effort" and on this repo it skipped most hours, so it has been
removed: **cron-job.org is the only trigger.** If that job stops, nothing scans.
Every 30 minutes uses ~1,490 of the 2,000 free Actions minutes a month (each run rounds up to
1 minute). Don't go more often: when the minutes run out, Actions stops until next month.

1. **GitHub token:** github.com → Settings → Developer settings → Personal access tokens →
   **Fine-grained tokens** → Generate. Repository access: only `short-alert`. Permissions:
   **Actions: Read and write** (nothing else). Pick an expiry and set a reminder to renew it.
2. **cron-job.org:** sign up (free) → Create cronjob:
   - URL: `https://api.github.com/repos/blanchy21/short-alert/actions/workflows/short-alert.yml/dispatches`
   - Schedule: custom `7,37 * * * *` (every 30 minutes)
   - Advanced → Request method **POST**, headers:
     - `Accept: application/vnd.github+json`
     - `Authorization: Bearer <your token>`
     - `X-GitHub-Api-Version: 2022-11-28`
   - Request body: `{"ref":"main"}`
3. Save, then use **Test run**: it should return **204**, and a new run appears in the Actions tab.

## Paper / live switch

Repo → **Settings → Secrets and variables → Actions → Variables** tab:

| Variable | Values | Default |
|---|---|---|
| `TRADING_MODE` | `paper` or `live` | `paper` |
| `HL_NETWORK` | `testnet` or `mainnet` | `mainnet` |
| `HL_ACCOUNT_ADDRESS` | your main Hyperliquid wallet address (0x…) | — |

And one **secret**: `HL_API_PRIVATE_KEY` — the private key of a Hyperliquid **API wallet**
(app.hyperliquid.xyz → More → API → Generate). An API wallet can trade but cannot withdraw.

### Sizing and caps (same as Grokbot's Short Seller)
The **pot** is the live account value, with unrealised gains ignored and losses counted
(paper mode starts from `PAPER_START_POT` = $58), so trades grow only as the account grows.
- risk up to **10% of the pot** per trade (the loss if the stop hits)
- each short uses at most **25% of the pot as margin** — in practice this limits most trades to less than 10% risk
- up to **5× isolated**, stepped down so liquidation sits at least 1.5× the stop distance away
- at most **3 open shorts** (positions opened elsewhere on the account count too)
- all open shorts at their stops + today's realised losses ≤ **20% of the day-start pot**; trades are shrunk or skipped to fit
- **daily stop** at a 20% loss of the day-start pot — nothing new until the next Dublin day
- BTC and ETH excluded; funding below −0.01%/h skipped

In live mode each alert:
1. opens a market short at that size
2. places a reduce-only **stop-loss** and **TP1** on the exchange straight away
   (if either is rejected, the position is closed immediately)
3. closes the position after 24h if neither has hit; real P&L (after fees) goes into the tally

Trades under Hyperliquid's $10 minimum, or on a coin already held, are skipped. Setting `TRADING_MODE` back to `paper` stops new live trades;
live trades already open keep being managed until they close.

**Check the setup:** Actions → short-alert → Run workflow → tick the test box. It sends a Telegram
test and shows the Hyperliquid account value it can see. Places no orders.

**Go live in two steps:** first `HL_NETWORK=testnet` (use a testnet API wallet and testnet funds
from app.hyperliquid-testnet.xyz) with `TRADING_MODE=live`, watch a trade or two, then switch to `mainnet`.

## Changing the rules
All thresholds are at the top of `short_alert.py` (`MIN_SCORE`, `MAX_STOP_PCT`, `BTC_EMA_PERIOD`, etc.).
