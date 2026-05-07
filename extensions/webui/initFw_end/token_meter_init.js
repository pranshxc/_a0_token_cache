/**
 * initFw_end/token_meter_init.js
 * Registers Alpine 'tokenMeter' store and fetches initial data.
 * Called once by A0's initFw_end extension hook after Alpine is ready.
 */
export default async function initTokenMeter() {
  try {
    // wait for Alpine to be available
    let tries = 0;
    while (!window.Alpine && tries++ < 50) {
      await new Promise(r => setTimeout(r, 100));
    }
    if (!window.Alpine) return;

    if (!window.Alpine.store('tokenMeter')) {
      window.Alpine.store('tokenMeter', {
        totals:      { input:0, output:0, cache_read:0, cache_write:0, cost:0.0, calls:0 },
        last:        null,
        history:     [],
        prices:      { input:0, output:0, cache_read:0, cache_write:0 },
        lastUpdated: 0,
        pricingSet() {
          return this.prices.input > 0 || this.prices.output > 0;
        },
        fmtCost(usd) {
          if (!this.pricingSet()) return '—';
          if (usd < 0.0001) return '$' + usd.toFixed(6);
          return '$' + usd.toFixed(4);
        },
        cachePct(inp, cr) {
          if (!inp) return '0%';
          return (100 * cr / inp).toFixed(1) + '%';
        },
        savings() {
          const cr = this.totals.cache_read;
          return cr * (this.prices.input - this.prices.cache_read) / 1e6;
        },
      });
    }

    // fetch initial data
    try {
      const res = await fetch('/api/token_meter_data');
      const data = await res.json();
      if (data.ok) {
        const s = window.Alpine.store('tokenMeter');
        s.totals  = data.totals;
        s.history = data.history;
        s.prices  = data.prices;
        if (data.history && data.history.length > 0) {
          s.last = data.history[data.history.length - 1];
        }
        s.lastUpdated = Date.now();
      }
    } catch (_) {}

  } catch (e) {
    console.error('[TokenMeter] init error', e);
  }
}
