/**
 * Deterministic test for the deferred Google tag loader (oi-228).
 *
 * Runs the ACTUAL inline script emitted into dist/ inside a fake DOM, so the
 * thing under test is the shipped bytes rather than a copy of the source. A
 * browser cannot isolate these branches: on a fast local server the idle
 * callback fires before a synthetic interaction can be dispatched, which is
 * exactly what happened while building this.
 *
 * What must hold:
 *   1. Nothing is requested at parse time. The tag is off the critical path.
 *   2. The gtag stub and both destination configs are queued on dataLayer
 *      immediately, so events fired before the library arrives replay on load.
 *   3. The idle path waits for the LOAD event, never runs before it.
 *   4. A user interaction loads the tag immediately, without waiting for idle.
 *   5. It loads exactly once no matter how many triggers fire.
 *   6. mrTrackConversion forces the loader up and queues the conversion.
 *
 *   node scripts/test_deferred_gtag.mjs
 */
import { readFileSync } from 'node:fs';
import { strict as assert } from 'node:assert';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const HTML = readFileSync(path.join(ROOT, 'dist', 'lp', 'strategy-call', 'index.html'), 'utf8');

// Pull the two inline scripts under test straight out of the build output.
function inlineScriptContaining(needle) {
  for (const m of HTML.matchAll(/<script(?![^>]*\ssrc=)[^>]*>([\s\S]*?)<\/script>/g)) {
    if (m[1].includes(needle)) return m[1];
  }
  throw new Error('no inline script containing ' + JSON.stringify(needle) + ' in the build output');
}
const LOADER = inlineScriptContaining('mrLoadGtag');
const CONV = inlineScriptContaining('mrTrackConversion');

function makeEnv() {
  const env = {
    listeners: {},
    appended: [],
    idleCallbacks: [],
    timeouts: [],
  };
  const document = {
    readyState: 'loading',
    createElement: () => ({ set src(v) { this._src = v; }, get src() { return this._src; } }),
    head: { appendChild: (el) => env.appended.push(el.src) },
    getElementsByTagName: () => [{ parentNode: { insertBefore: () => {} } }],
  };
  const window = {
    document,
    dataLayer: undefined,
    addEventListener: (type, fn) => { (env.listeners[type] = env.listeners[type] || []).push(fn); },
    removeEventListener: () => {},
    requestIdleCallback: (fn) => env.idleCallbacks.push(fn),
    setTimeout: (fn) => env.timeouts.push(fn),
    Promise,
  };
  window.window = window;
  env.window = window;
  env.document = document;
  env.ctx = vm.createContext(window);
  return env;
}

function fire(env, type) {
  for (const fn of env.listeners[type] || []) fn({ type });
}

// ── 1 + 2: parse time ──────────────────────────────────────────────────────
let env = makeEnv();
vm.runInContext(LOADER, env.ctx);

assert.equal(env.appended.length, 0, 'no script may be requested at parse time');
assert.equal(typeof env.window.gtag, 'function', 'the gtag stub must exist immediately');
assert.equal(env.window.dataLayer.length, 3, 'js + two config calls must be queued immediately');
const queued = env.window.dataLayer.map((a) => Array.prototype.slice.call(a));
assert.equal(queued[1][1], 'G-L8T7ZPXTD5', 'GA4 destination must be configured');
assert.equal(queued[2][1], 'AW-18338412822', 'Ads destination must be configured');

// ── 3: the idle path is gated behind load ──────────────────────────────────
assert.equal(env.idleCallbacks.length, 0, 'idle must not be scheduled before the load event');
fire(env, 'load');
assert.equal(env.idleCallbacks.length, 1, 'load must schedule the idle callback');
assert.equal(env.appended.length, 0, 'scheduling is not loading');
env.idleCallbacks[0]();
assert.equal(env.appended.length, 1, 'the idle callback must load the tag');
assert.match(env.appended[0], /googletagmanager\.com\/gtag\/js\?id=AW-18338412822$/);

// ── 4: interaction loads immediately, without waiting for load or idle ─────
env = makeEnv();
vm.runInContext(LOADER, env.ctx);
assert.equal(env.appended.length, 0);
fire(env, 'pointerdown');
assert.equal(env.appended.length, 1, 'an interaction must load the tag straight away');
for (const type of ['keydown', 'touchstart', 'scroll', 'mousemove']) {
  assert.ok(env.listeners[type] && env.listeners[type].length, type + ' must be an interaction trigger');
}

// ── 5: loads exactly once however many triggers fire ───────────────────────
fire(env, 'keydown');
fire(env, 'scroll');
env.document.readyState = 'complete';
fire(env, 'load');
for (const cb of env.idleCallbacks) cb();
assert.equal(env.appended.length, 1, 'the tag must load exactly once');

// ── 6: a conversion forces the loader and queues the event ─────────────────
env = makeEnv();
vm.runInContext(LOADER, env.ctx);
vm.runInContext(CONV, env.ctx);
const beforeLen = env.window.dataLayer.length;
env.window.mrTrackConversion('BOOKING-1');
assert.equal(env.appended.length, 1, 'a conversion must force the tag up, not wait for idle');
const conv = env.window.dataLayer.slice(beforeLen).map((a) => Array.prototype.slice.call(a));
assert.equal(conv[0][1], 'conversion');
assert.equal(conv[0][2].send_to, 'AW-18338412822/g7y6CNbl0dMcEJbyt6hE');
assert.equal(conv[0][2].transaction_id, 'BOOKING-1');
assert.equal(conv[1][1], 'book_strategy_call');

// A conversion with no tag available at all must still not throw: a blocked
// or failed tag must never break a booking.
env = makeEnv();
vm.runInContext(CONV, env.ctx);
env.window.mrTrackConversion('BOOKING-2');

console.log('deferred gtag loader ok (6 behaviours, run against dist/)');
