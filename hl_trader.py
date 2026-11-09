"""
Hyperliquid order placement for Short Alert (live mode only).

Opens a market short, then places a reduce-only stop-loss and take-profit on the
exchange so they protect the position between hourly runs. Uses an API (agent)
wallet: it can trade but cannot withdraw.

Needs:
  HL_ACCOUNT_ADDRESS   your main Hyperliquid wallet address (0x...)
  HL_API_PRIVATE_KEY   the API wallet's private key
  HL_NETWORK           "mainnet" (default) or "testnet"
"""

import os
import time

import eth_account
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants

MIN_NOTIONAL_USD = 10.0      # Hyperliquid's minimum order value
ENTRY_SLIPPAGE = 0.01        # max 1% worse than mid on the market entry


class TraderError(Exception):
    pass


def _statuses(resp) -> list:
    if not isinstance(resp, dict) or resp.get("status") != "ok":
        raise TraderError(f"exchange rejected request: {resp}")
    return resp["response"]["data"]["statuses"]


class Trader:
    def __init__(self):
        addr = os.environ.get("HL_ACCOUNT_ADDRESS", "").strip()
        key = os.environ.get("HL_API_PRIVATE_KEY", "").strip()
        if not addr or not key:
            raise TraderError("HL_ACCOUNT_ADDRESS / HL_API_PRIVATE_KEY not set")
        self.network = os.environ.get("HL_NETWORK", "mainnet").strip().lower()
        url = constants.TESTNET_API_URL if self.network == "testnet" else constants.MAINNET_API_URL
        self.address = addr
        self.info = Info(url, skip_ws=True)
        self.signer = eth_account.Account.from_key(key).address
        self.exchange = Exchange(eth_account.Account.from_key(key), url, account_address=addr)
        self.check_agent()

    def check_agent(self) -> None:
        """Fail early if the API wallet isn't approved for this account (orders would be rejected)."""
        if self.signer.lower() == self.address.lower():
            return  # signing with the main wallet itself
        try:
            role = self.info.post("/info", {"type": "userRole", "user": self.signer})
        except Exception:
            return  # can't check; let the order attempt report any problem
        owner = (role.get("data") or {}).get("user", "") if isinstance(role, dict) else ""
        if role.get("role") != "agent" or owner.lower() != self.address.lower():
            raise TraderError(
                f"API wallet {self.signer[:6]}…{self.signer[-4:]} is not approved for account "
                f"{self.address[:6]}…{self.address[-4:]} on {self.network}. Approve it on Hyperliquid "
                f"(More → API → Authorize), or save the key of an approved API wallet.")

    # ------------------------------------------------------------ rounding
    def _sz_decimals(self, coin: str) -> int:
        return self.info.asset_to_sz_decimals[self.info.name_to_asset(coin)]

    def round_px(self, coin: str, px: float) -> float:
        # Perps: max 5 significant figures and max (6 - szDecimals) decimals
        return round(float(f"{px:.5g}"), 6 - self._sz_decimals(coin))

    def round_sz(self, coin: str, sz: float) -> float:
        return round(sz, self._sz_decimals(coin))

    # ------------------------------------------------------------ account
    def account_value(self) -> float:
        return float(self.info.user_state(self.address)["marginSummary"]["accountValue"])

    def unified(self) -> bool:
        """True if the account uses Hyperliquid's unified account (perps margined from spot USDC)."""
        try:
            return self.info.post("/info", {"type": "userAbstraction", "user": self.address}) == "unifiedAccount"
        except Exception:
            return False

    def _dexes(self) -> list:
        """Names of Hyperliquid's extra perp markets (HIP-3, e.g. "xyz", "io"); the main market is ""."""
        if not hasattr(self, "_dex_names"):
            try:
                self._dex_names = [d["name"] for d in self.info.post("/info", {"type": "perpDexs"}) if d]
            except Exception:
                self._dex_names = []
        return self._dex_names

    def all_positions(self) -> list:
        """Open positions on every perp market: the main one plus HIP-3 markets (e.g. xyz:NVDA)."""
        out = []
        for dex in [""] + self._dexes():
            try:
                st = self.info.post("/info", {"type": "clearinghouseState", "user": self.address, "dex": dex})
            except Exception:
                if dex == "":
                    raise
                continue  # one extra market not answering shouldn't stop the scan
            out += [p["position"] for p in st.get("assetPositions", []) if float(p["position"]["szi"]) != 0]
        return out

    def pot(self) -> float:
        """Account value with unrealised gains ignored and unrealised losses counted (per position)."""
        if self.unified():
            # Collateral is the spot USDC balance. It already includes the unrealised P&L of open positions
            # on every perp market (main and HIP-3), so take each position's gain back out; losses stay in.
            gains = sum(max(0.0, float(p.get("unrealizedPnl") or 0)) for p in self.all_positions())
            usdc = sum(float(b["total"]) for b in self.info.spot_user_state(self.address)["balances"]
                       if b["coin"] == "USDC")
            return usdc - gains
        us = self.info.user_state(self.address)
        gains = sum(max(0.0, float(p["position"].get("unrealizedPnl") or 0)) for p in us["assetPositions"])
        return float(us["marginSummary"]["accountValue"]) - gains

    def open_coins(self) -> set:
        """Coins with an open position on any perp market (HIP-3 ones keep their prefix, e.g. "xyz:NVDA")."""
        return {p["coin"] for p in self.all_positions()}

    def position(self, coin: str) -> float:
        """Signed size (negative = short); 0 if flat."""
        for p in self.info.user_state(self.address)["assetPositions"]:
            if p["position"]["coin"] == coin:
                return float(p["position"]["szi"])
        return 0.0

    def mid(self, coin: str) -> float:
        return float(self.info.all_mids()[coin])

    def cancel_all(self, coin: str) -> None:
        for o in self.info.open_orders(self.address):
            if o["coin"] == coin:
                self.exchange.cancel(coin, o["oid"])

    # ------------------------------------------------------------ trading
    def open_short(self, coin: str, notional_usd: float, leverage: int, stop_pct: float, tp_pct: float,
                   tp2_pct: float | None = None, tp1_fraction: float = 0.5) -> dict:
        """
        notional_usd: position value to open (sized by short_alert.size_trade)
        leverage:     isolated leverage (margin = notional / leverage)
        stop_pct:     stop distance above entry in % (positive)
        tp_pct:       TP1 distance below entry in % (positive)
        tp2_pct:      TP2 distance below entry in % (positive); None = whole position at TP1
        tp1_fraction: share of the position closed at TP1 when TP2 is used
        """
        if self.position(coin) != 0:
            raise TraderError(f"already have a {coin} position on the exchange")

        mid = self.mid(coin)
        sz = self.round_sz(coin, notional_usd / mid)
        if sz * mid < MIN_NOTIONAL_USD:
            raise TraderError(f"position ${sz * mid:.2f} is under Hyperliquid's ${MIN_NOTIONAL_USD:.0f} minimum")

        lev = self.exchange.update_leverage(leverage, coin, is_cross=False)
        if not isinstance(lev, dict) or lev.get("status") != "ok":
            raise TraderError(f"couldn't set {leverage}x isolated leverage: {lev}")

        st = _statuses(self.exchange.market_open(coin, False, sz, None, ENTRY_SLIPPAGE))[0]
        if "filled" not in st:
            raise TraderError(f"entry not filled: {st}")
        entry = float(st["filled"]["avgPx"])
        filled = float(st["filled"]["totalSz"])

        stop = self.round_px(coin, entry * (1 + stop_pct / 100))
        tp = self.round_px(coin, entry * (1 - tp_pct / 100))

        # 1. Stop-loss first, on its own. Without it the position is closed straight away.
        try:
            sl_err = self._place_trigger(coin, filled, stop, "sl")
        except Exception as e:
            sl_err = f"{type(e).__name__}: {e}"
        if sl_err:
            try:
                self.close(coin)
                closed = "position closed straight away"
            except Exception as e:
                closed = f"CLOSING ALSO FAILED ({e}) - CLOSE {coin} BY HAND"
            raise TraderError(f"stop-loss rejected ({sl_err}); {closed}")

        # 2. Take-profits. If these fail the position stays open, protected by the stop.
        tp2 = self.round_px(coin, entry * (1 - tp2_pct / 100)) if tp2_pct else None
        tp1_sz = self.round_sz(coin, filled * tp1_fraction) if tp2 else filled
        tp2_sz = self.round_sz(coin, filled - tp1_sz) if tp2 else 0
        if tp2 and (tp1_sz * entry < MIN_NOTIONAL_USD or tp2_sz * entry < MIN_NOTIONAL_USD or tp2 >= tp):
            tp2, tp1_sz, tp2_sz = None, filled, 0   # too small to split: whole position at TP1
        errs = []
        for px, part, kind in ((tp, tp1_sz, "TP1"), (tp2, tp2_sz, "TP2")):
            if not px:
                continue
            try:
                e = self._place_trigger(coin, part, px, "tp")
            except Exception as ex:
                e = f"{type(ex).__name__}: {ex}"
            if e:
                errs.append(f"{kind}: {e}")
        tp_err = "; ".join(errs) or None

        return {"entry": entry, "size": filled, "stop": stop, "tp1": tp, "leverage": leverage, "tp_error": tp_err,
                "tp2": tp2, "tp1_size": tp1_sz, "tp2_size": tp2_sz,
                "notional": round(entry * filled, 2), "risk_usd": round((stop - entry) * filled, 2),
                "network": self.network}

    def _place_trigger(self, coin: str, sz: float, trigger_px: float, kind: str) -> str | None:
        """Place one reduce-only market trigger order to buy back a short. Returns an error string or None."""
        slip = 1.10 if kind == "sl" else 1.05   # worst fill price allowed once triggered
        resp = self.exchange.order(
            coin, True, sz, self.round_px(coin, trigger_px * slip),
            {"trigger": {"triggerPx": trigger_px, "isMarket": True, "tpsl": kind}},
            reduce_only=True)
        if not isinstance(resp, dict) or resp.get("status") != "ok":
            return f"exchange replied {resp}"
        statuses = (resp.get("response") or {}).get("data", {}).get("statuses") or []
        if not statuses:
            return f"no order status in reply {resp}"
        if "error" in statuses[0]:
            return statuses[0]["error"]
        return None

    def move_stop(self, coin: str, new_stop: float, tp2: float | None) -> float:
        """After TP1: cancel the old orders, put the stop at new_stop (and TP2 back) for what's left.
        Returns the new stop price. If the stop can't be placed, closes the rest."""
        remaining = abs(self.position(coin))
        if remaining == 0:
            return new_stop
        self.cancel_all(coin)
        new_stop = self.round_px(coin, new_stop)
        err = self._place_trigger(coin, remaining, new_stop, "sl")
        if err:
            self.close(coin)
            raise TraderError(f"break-even stop rejected ({err}); rest of position closed")
        if tp2:
            err = self._place_trigger(coin, remaining, self.round_px(coin, tp2), "tp")
            if err:
                raise TraderError(f"TP2 re-place rejected ({err}); break-even stop is in place")
        return new_stop

    def close(self, coin: str) -> None:
        self.cancel_all(coin)
        if self.position(coin) != 0:
            _statuses(self.exchange.market_close(coin))

    def closing_fills(self, coin: str, since_ms: int) -> dict | None:
        """Summarise fills that closed our short since entry (P&L after open+close fees); None if none yet."""
        fills = [f for f in self.info.user_fills_by_time(self.address, since_ms - 5000)
                 if f["coin"] == coin and f.get("dir") in ("Open Short", "Close Short")]
        closes = [f for f in fills if f["dir"] == "Close Short"]
        if not closes:
            return None
        sz = sum(float(f["sz"]) for f in closes)
        px = sum(float(f["px"]) * float(f["sz"]) for f in closes) / sz
        pnl = sum(float(f["closedPnl"]) for f in closes) - sum(float(f["fee"]) for f in fills)
        last = max(closes, key=lambda f: int(f["time"]))
        return {"exit": px, "last_px": float(last["px"]), "pnl_usd": round(pnl, 2)}

    def wait_flat(self, coin: str, tries: int = 5) -> bool:
        for _ in range(tries):
            if self.position(coin) == 0:
                return True
            time.sleep(1)
        return False
