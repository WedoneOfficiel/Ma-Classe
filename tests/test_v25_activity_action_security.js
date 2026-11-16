const fs = require("fs");
const vm = require("vm");
const assert = require("assert");

const source = fs.readFileSync("_all.js", "utf8");
assert(!source.includes("new Function("), "application data must never be executed as generated JavaScript");
assert(!source.includes('onclick="${x.action}"'), "student activity must not inject action strings into HTML");
assert(!source.includes('onclick="${n.action}"'), "student notifications must not inject action strings into HTML");
assert(source.includes('const jsObjectArg=value=>'), "object arguments need an HTML-safe serializer");
assert(source.includes("runActivityAction(${jsObjectArg(x.action)})"));
assert(source.includes("runActivityAction(${jsObjectArg(n.action)})"));

const start = source.indexOf("function runActivityAction(action){");
const end = source.indexOf("\nfunction openActivityItem", start);
assert(start >= 0 && end > start, "typed activity action dispatcher must exist");
const dispatcher = source.slice(start, end);

const sandbox = {
  window: {},
  opened: [],
  navigated: [],
  openWorkTracking: id => sandbox.opened.push(["workTracking", id]),
  openEvaluation: id => sandbox.opened.push(["evaluation", id]),
  openStudentWork: id => sandbox.opened.push(["studentWork", id]),
  printBulletin: id => sandbox.opened.push(["bulletin", id]),
  openStudentBulletinNotification: (id, date) => sandbox.opened.push(["studentBulletin", id, date]),
  openAttendance: id => sandbox.opened.push(["attendance", id]),
  go: page => sandbox.navigated.push(page)
};
vm.runInNewContext(dispatcher, sandbox);

const payload = "x');globalThis.pwned=true;//&quot; <svg onload=alert(1)>";
sandbox.runActivityAction({ type: "openStudentWork", id: payload });
assert.strictEqual(sandbox.opened.length, 1);
assert.strictEqual(sandbox.opened[0][1], payload, "untrusted IDs must be passed as inert data");
assert.strictEqual(sandbox.pwned, undefined, "malicious IDs must never execute");

sandbox.runActivityAction({ type: "mail", id: payload, page: "studentMessages" });
assert.strictEqual(sandbox.window.mailV2Selected, payload);
assert.strictEqual(sandbox.window.mailV2Folder, "inbox");
assert.strictEqual(sandbox.navigated.at(-1), "studentMessages");

sandbox.runActivityAction({ type: "cloud", id: payload, page: "studentDocuments" });
assert.strictEqual(sandbox.window.cloudSelected, payload);
assert.strictEqual(sandbox.window.cloudPath.length, 0);
assert.strictEqual(sandbox.navigated.at(-1), "studentDocuments");

const count = sandbox.navigated.length;
sandbox.runActivityAction({ type: "go", page: "javascript:alert(1)" });
sandbox.runActivityAction({ type: "eval", code: "globalThis.pwned=true" });
assert.strictEqual(sandbox.navigated.length, count, "unknown actions and pages must be ignored");
assert.strictEqual(sandbox.pwned, undefined);

console.log("OK — actions de notifications typées, liste blanche et résistantes aux identifiants malveillants.");
