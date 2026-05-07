/**
 * Receives token_meter_update events pushed over WebSocket
 * and updates the Alpine store so the panel refreshes live.
 */
export default async function tokenMeterWsPush(ctx) {
  try {
    if (ctx?.data?.type !== "token_meter_update") return;
    const store = window.Alpine?.store("tokenMeter");
    if (!store) return;
    const { totals, last, history, prices } = ctx.data;
    store.totals  = totals  ?? store.totals;
    store.last    = last    ?? store.last;
    store.history = history ?? store.history;
    store.prices  = prices  ?? store.prices;
    store.lastUpdated = Date.now();
  } catch(e) {
    console.error("[TokenMeter] WS push error", e);
  }
}
