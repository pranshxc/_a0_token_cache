"""
monologue_end -> _60_token_meter

Extracts usage_metadata from last AIMessage after every LLM call.
Stores data in context.data for the API endpoint + pushes WS event.
"""
from __future__ import annotations
import os, json, time
from helpers.extension import Extension
from agent import LoopData

METER_DIR = os.path.join("work", "token_meter")

def _cfg(key, default):
    env_val = os.environ.get(f"TOKEN_METER_{key.upper()}")
    if env_val is not None:
        if isinstance(default, bool): return env_val.lower() in ("1","true","yes")
        if isinstance(default, float):
            try: return float(env_val)
            except: pass
        return env_val
    try:
        import yaml
        p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..","..","default_config.yaml"))
        with open(p) as f: data = yaml.safe_load(f) or {}
        v = data.get(key, default)
        return float(v) if isinstance(default, float) else v
    except: return default

ENABLED           = _cfg("enabled",              True)
WRITE_JSONL       = _cfg("write_jsonl",            True)
PRICE_IN          = float(_cfg("price_input_per_1m",       0.0))
PRICE_OUT         = float(_cfg("price_output_per_1m",      0.0))
PRICE_CACHE_READ  = float(_cfg("price_cache_read_per_1m",  0.0))
PRICE_CACHE_WRITE = float(_cfg("price_cache_write_per_1m", 0.0))

def _session_id(agent):
    try:
        s = getattr(agent,"chat_id",None) or getattr(agent.context,"id",None)
        return str(s)[:32] if s else "default"
    except: return "default"

def _model_name(agent):
    try: return str(agent.config.chat_model.name)
    except:
        try: return str(agent.config.chat_model)
        except: return "unknown"

def _extract_usage(agent):
    try:
        for msg in reversed(agent.history.output()):
            um = getattr(msg,"usage_metadata",None)
            if not um and isinstance(msg,dict): um = msg.get("usage_metadata") or msg.get("usage")
            if um and isinstance(um,dict) and "input_tokens" in um:
                return {
                    "input":       int(um.get("input_tokens",0)),
                    "output":      int(um.get("output_tokens",0)),
                    "cache_read":  int(um.get("cache_read_input_tokens",0)),
                    "cache_write": int(um.get("cache_creation_input_tokens",0)),
                }
    except: pass
    return {"input":0,"output":0,"cache_read":0,"cache_write":0}

def _cost(inp,out,cr,cw):
    return inp*PRICE_IN/1e6 + out*PRICE_OUT/1e6 + cr*PRICE_CACHE_READ/1e6 + cw*PRICE_CACHE_WRITE/1e6

def _get_totals(ctx):
    return ctx.data.get("_token_meter_totals",
        {"input":0,"output":0,"cache_read":0,"cache_write":0,"cost":0.0,"calls":0})

def _get_history(ctx):
    return ctx.data.get("_token_meter_history", [])

def _append_jsonl(sid, rec):
    try:
        os.makedirs(METER_DIR, exist_ok=True)
        with open(os.path.join(METER_DIR,f"{sid}.jsonl"),"a",encoding="utf-8") as f:
            f.write(json.dumps(rec)+"\n")
    except: pass


class TokenMeter(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not ENABLED or not self.agent or self.agent.number != 0:
            return
        try:
            agent   = self.agent
            ctx     = agent.context
            sid     = _session_id(agent)
            model   = _model_name(agent)
            usage   = _extract_usage(agent)
            inp, out, cr, cw = usage["input"], usage["output"], usage["cache_read"], usage["cache_write"]

            if inp == 0 and out == 0:
                return

            call_cost = _cost(inp, out, cr, cw)
            ts        = time.time()

            # update totals
            t = _get_totals(ctx)
            t["input"]      += inp;  t["output"]      += out
            t["cache_read"] += cr;   t["cache_write"] += cw
            t["cost"]       += call_cost; t["calls"]  += 1
            ctx.data["_token_meter_totals"] = t

            # keep last 50 calls in history
            hist = _get_history(ctx)
            hist.append({
                "call":          t["calls"],
                "ts":            round(ts),
                "model":         model,
                "input":         inp,
                "output":        out,
                "cache_read":    cr,
                "cache_write":   cw,
                "cost_usd":      round(call_cost, 6),
                "cache_hit_pct": round(100*cr/inp, 1) if inp > 0 else 0,
            })
            ctx.data["_token_meter_history"] = hist[-50:]

            # JSONL
            if WRITE_JSONL:
                _append_jsonl(sid, {"session": sid, **hist[-1]})

            # push websocket event so UI updates live
            try:
                payload = {
                    "type":    "token_meter_update",
                    "totals":  t,
                    "last":    hist[-1],
                    "history": ctx.data["_token_meter_history"],
                    "prices":  {"input": PRICE_IN, "output": PRICE_OUT,
                                "cache_read": PRICE_CACHE_READ, "cache_write": PRICE_CACHE_WRITE},
                }
                await ctx.communicate(payload)
            except Exception:
                pass

        except Exception as exc:
            try:
                self.agent.context.log.log(type="hint", heading="⚠️ Token Meter Error", content=str(exc))
            except: pass
