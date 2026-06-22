import assert from "node:assert/strict";
import test from "node:test";

import {
  PENDING_REVIEW_COUNT_CHANGED_EVENT,
  normalizePendingReviewCount,
  notifyPendingReviewCountChanged,
} from "./pending-review-notifications.js";

test("normalizes pending review counts from the API", () => {
  assert.equal(normalizePendingReviewCount(7), 7);
  assert.equal(normalizePendingReviewCount(-1), 0);
  assert.equal(normalizePendingReviewCount("invalid"), 0);
});

test("notifies listeners after a review decision", () => {
  const target = new EventTarget();
  let notificationCount = 0;
  target.addEventListener(PENDING_REVIEW_COUNT_CHANGED_EVENT, () => {
    notificationCount += 1;
  });

  notifyPendingReviewCountChanged(target);

  assert.equal(notificationCount, 1);
});
