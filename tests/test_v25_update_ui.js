#!/usr/bin/env node
const fs = require('fs');
const assert = require('assert');
const source = fs.readFileSync('_all.js', 'utf8');
assert(source.includes("function maintenanceBanner()"));
assert(source.includes("api('/api/update-maintenance')"));
assert(source.includes("function scheduleUpdate()"));
assert(source.includes("function cancelScheduledUpdate()"));
assert(source.includes("Installer maintenant"));
assert(source.includes("Les modifications non enregistrées pourraient être perdues."));
assert(source.includes("authCanManage()"));
console.log("OK — carte de mise à jour direction, programmation, annulation et bannière multi-rôles.");
