/**
 * webui_ws_push/token_meter_ws.js
 * Receives token_meter_update WS events and refreshes Alpine store.
 */
export default async function tokenMeterWsPush(ctx) {
  try {
    if (!ctx || ctx?.type !== 'token_meter_update') return;
    const s = window.Alpine?.store('tokenMeter');
    if (!s) return;
    if (ctx.totals)  s.totals  = ctx.totals;
    if (ctx.last)    s.last    = ctx.last;
    if (ctx.history) s.history = ctx.history;
    if (ctx.prices)  s.prices  = ctx.prices;
    s.lastUpdated = Date.now();
  } catch (e) {
    console.error('[TokenMeter] WS push error', e);
  }
}
