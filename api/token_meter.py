"""
GET /api/token_meter_data
Returns session totals, per-call history, and pricing config.
Bound automatically via A0's api/ plugin discovery.
"""
from __future__ import annotations
import os
from helpers.api import ApiHandler, Request, Response

PRICE_IN          = float(os.environ.get("TOKEN_METER_PRICE_INPUT_PER_1M",       0.0))
PRICE_OUT         = float(os.environ.get("TOKEN_METER_PRICE_OUTPUT_PER_1M",      0.0))
PRICE_CACHE_READ  = float(os.environ.get("TOKEN_METER_PRICE_CACHE_READ_PER_1M",  0.0))
PRICE_CACHE_WRITE = float(os.environ.get("TOKEN_METER_PRICE_CACHE_WRITE_PER_1M", 0.0))


class TokenMeterData(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            ctx = self.context
            totals  = ctx.data.get("_token_meter_totals",
                        {"input":0,"output":0,"cache_read":0,"cache_write":0,"cost":0.0,"calls":0})
            history = ctx.data.get("_token_meter_history", [])
            return {
                "ok":      True,
                "totals":  totals,
                "history": history,
                "prices": {
                    "input":       PRICE_IN,
                    "output":      PRICE_OUT,
                    "cache_read":  PRICE_CACHE_READ,
                    "cache_write": PRICE_CACHE_WRITE,
                },
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
