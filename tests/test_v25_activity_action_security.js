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

const eventHandlers = [...source.matchAll(/on[a-z]+="([^"]*)"/gi)].map(match => match[1]);
assert(!eventHandlers.some(handler => /'\$\{[^}]+\}'/.test(handler)),
  "inline event handlers must not interpolate untrusted values inside raw JavaScript strings");
const unsafeDataAttributes = [...source.matchAll(/\b(?:data-[\w-]+|value|id|title|name|for|aria-[\w-]+)="([^"]*\$\{[^}]+\}[^"]*)"/g)]
  .filter(match => !/\$\{(?:esc|jsArg|jsObjectArg)\(/.test(match[1]));
assert.strictEqual(unsafeDataAttributes.length, 0, "dynamic HTML data/value attributes must be escaped");

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


const uploadStart = source.indexOf("const safeUploadUrl=value=>");
const uploadEnd = source.indexOf(";\nconst safeRichHtml", uploadStart) + 1;
assert(uploadStart >= 0 && uploadEnd > uploadStart, "shared upload URL validator must exist");
const mailSandbox = {};
vm.runInNewContext(source.slice(uploadStart, uploadEnd) + ";globalThis.safeUploadUrl=safeUploadUrl;", mailSandbox);
const mailStart = source.indexOf("function safeMailAttachmentUrl(value){");
const mailEnd = source.indexOf("\n  window.mailV2104PreviewAttachment", mailStart);
assert(mailStart >= 0 && mailEnd > mailStart, "mail attachment URL wrapper must exist");
vm.runInNewContext(source.slice(mailStart, mailEnd) + ";globalThis.safeMailAttachmentUrl=safeMailAttachmentUrl;", mailSandbox);
const safePath = "/data/uploads/mail-v2/teacher:t1/report.pdf";
assert.strictEqual(mailSandbox.safeUploadUrl(safePath), safePath);
assert.strictEqual(mailSandbox.safeMailAttachmentUrl(safePath), safePath);
for (const bad of [
  "javascript:alert(1)//data/uploads/mail-v2/teacher:t1/file.pdf",
  "https://evil.example/data/uploads/mail-v2/teacher:t1/file.pdf",
  "//evil.example/data/uploads/mail-v2/teacher:t1/file.pdf",
  "/data/uploads/mail-v2/teacher:t1/%2e%2e/secret.pdf",
  "/data/uploads/mail-v2/teacher:t1/%5c..%5csecret.pdf",
  "/data/uploads/mail-v2/teacher:t1/file.pdf?x=1",
  "/data/uploads/mail-v2/teacher:t1/file.pdf#x"
]) {
  assert.strictEqual(mailSandbox.safeUploadUrl(bad), "", "unsafe upload URL must be rejected");
  assert.strictEqual(mailSandbox.safeMailAttachmentUrl(bad), "", "unsafe mail attachment URL must be rejected");
}

console.log("OK — actions de notifications typées, liste blanche et résistantes aux identifiants malveillants.");
