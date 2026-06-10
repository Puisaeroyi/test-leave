import assert from "node:assert/strict";
import test from "node:test";

import {
  calculateHourRange,
  getCustomHourOffsets,
  inferCustomHourOffsets,
} from "./time-utils.js";

test("calculates a daytime custom-hour range", () => {
  assert.equal(calculateHourRange(9, 13), 4);
});

test("calculates an overnight custom-hour range", () => {
  assert.equal(calculateHourRange(22, 6), 8);
});

test("treats equal start and end hours as an empty range", () => {
  assert.equal(calculateHourRange(6, 6), 0);
});

test("places second-half night-shift hours on the next calendar day", () => {
  assert.deepEqual(getCustomHourOffsets(2, 6, 1), { startDayOffset: 1, endDayOffset: 1 });
});

test("moves overnight end time to the following calendar day", () => {
  assert.deepEqual(getCustomHourOffsets(22, 6, 0), { startDayOffset: 0, endDayOffset: 1 });
});

test("uses shift minutes when mapping night-shift hours to calendar days", () => {
  assert.deepEqual(
    inferCustomHourOffsets(22, 6, { start_time: "22:30", end_time: "06:30" }),
    { startDayOffset: 1, endDayOffset: 2 },
  );
});
