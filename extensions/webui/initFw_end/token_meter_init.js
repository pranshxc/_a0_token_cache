/**
 * Initialises the Alpine 'tokenMeter' store and registers the
 * token-meter-panel web component used by the right canvas surface.
 */
export default async function initTokenMeter() {
  try {
    // --- Alpine store ---
    if (window.Alpine) {
      if (!window.Alpine.store("tokenMeter")) {
        window.Alpine.store("tokenMeter", {
          totals:      { input:0, output:0, cache_read:0, cache_write:0, cost:0, calls:0 },
          last:        null,
          history:     [],
          prices:      { input:0, output:0, cache_read:0, cache_write:0 },
          lastUpdated: 0,
          pricingSet() {
            return this.prices.input > 0 || this.prices.output > 0;
          },
          fmtCost(usd) {
            if (!this.pricingSet()) return "—";
            if (usd < 0.0001) return `$${usd.toFixed(6)}`;
            return `$${usd.toFixed(4)}`;
          },
          cachePct(inp, cr) {
            if (!inp) return "0%";
            return (100*cr/inp).toFixed(1) + "%";
          },
          cacheWorking() {
            return (this.totals.cache_read > 0 || this.totals.cache_write > 0);
          },
          savings() {
            const cr = this.totals.cache_read;
            return cr * (this.prices.input - this.prices.cache_read) / 1e6;
          },
          barW(val, total) {
            if (!total) return "0%";
            return Math.min(100, Math.round(100*val/total)) + "%";
          },
        });
      }
    }

    // initial data fetch
    try {
      const res  = await fetch("/api/token_meter_data");
      const data = await res.json();
      if (data.ok) {
        const s = window.Alpine?.store("tokenMeter");
        if (s) {
          s.totals  = data.totals;
          s.history = data.history;
          s.prices  = data.prices;
          s.lastUpdated = Date.now();
        }
      }
    } catch(_) {}

  } catch(e) {
    console.error("[TokenMeter] init error", e);
  }
}
