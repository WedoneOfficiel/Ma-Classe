const fs = require("fs");
const vm = require("vm");
const assert = require("assert");

const source = fs.readFileSync("_all.js", "utf8");
const start = source.indexOf("function eventCard(o,d,studentMode=false){");
const end = source.indexOf("function startScheduleDrag", start);
assert(start >= 0 && end > start, "eventCard function must exist");
const eventCardSource = source.slice(start, end);

const sandbox = {
  iso: () => "2026-11-16",
  mins: () => 600,
  addHour: () => "11:00",
  subjectColor: () => ["#ffffff", "#dddddd", "#123456"],
  time: value => String(value),
  cls: () => ({ name: "6A" }),
  esc: value => String(value ?? "").replace(/[&<>"']/g, ch => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[ch]),
  openOccurrence: (...args) => { sandbox.opened = args; },
  startScheduleDrag: (_event, id) => { sandbox.dragged = id; },
  openSchedule: id => { sandbox.edited = id; }
};
vm.runInNewContext(eventCardSource, sandbox);

const payload = "x');globalThis.pwned=true;//<svg onload=alert(1)>";
const html = sandbox.eventCard({
  id: payload,
  classId: "c1",
  subject: "Maths",
  time: "10:00",
  endTime: "11:00",
  pattern: "none;position:fixed;inset:0"
}, new Date("2026-11-16T10:00:00"), false);

assert(html.includes("--event-pattern:none;"), "unknown patterns must fall back to none");
assert(!html.includes("position:fixed"), "untrusted pattern CSS must never be rendered");
assert(!html.includes("<svg onload=alert(1)>"), "untrusted IDs must not create HTML");

function decodeAttribute(value) {
  return value.replace(/&quot;/g, '"').replace(/&#39;/g, "'")
    .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
}
const click = html.match(/onclick="([^"]*)"/);
assert(click, "event card must keep its click action");
vm.runInNewContext(decodeAttribute(click[1]), sandbox);
assert.strictEqual(sandbox.opened[0], payload, "the original ID must be passed as data");
assert.strictEqual(sandbox.pwned, undefined, "ID text must not execute as JavaScript");

const drag = html.match(/ondragstart="([^"]*)"/);
assert(drag, "event card must keep its drag action");
vm.runInNewContext(decodeAttribute(drag[1]), sandbox);
assert.strictEqual(sandbox.dragged, payload, "drag handler must receive the original ID safely");

console.log("OK — timetable event IDs and patterns are safe against stored HTML/JS injection.");
