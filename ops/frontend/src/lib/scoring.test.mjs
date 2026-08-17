import { sortRows, efficiencyFloor } from "./scoring.js";
import assert from "node:assert";

const rows = [
  { submission_id: "a", team: "alpha", passed: 14, tokens: 186_000 },
  { submission_id: "b", team: "bravo", passed: 14, tokens: 121_500 },
  { submission_id: "c", team: "cheap", passed: 3, tokens: 9_200 },
  { submission_id: "d", team: "delta", passed: 9, tokens: 38_400 },
];
const passed = { sort: (r) => r.passed };
const tokens = { sort: (r) => r.tokens };

// Equal pass counts must rank the cheaper submission first, not the earlier name.
assert.deepEqual(sortRows(rows, passed, "desc").map((r) => r.team),
  ["bravo", "alpha", "delta", "cheap"]);
assert.deepEqual(sortRows(rows, tokens, "asc").map((r) => r.team),
  ["cheap", "delta", "bravo", "alpha"]);

assert.deepEqual(sortRows([], passed, "desc"), []);

// Floor is half the leader's score; the give-up submission sits below it.
assert.equal(efficiencyFloor(rows), 7);
assert.ok(rows.find((r) => r.team === "cheap").passed < efficiencyFloor(rows));
assert.equal(efficiencyFloor([]), 0);

console.log("sort + floor ok");
