export const PENDING_REVIEW_COUNT_CHANGED_EVENT = "pending-review-count-changed";

export const normalizePendingReviewCount = (value) => (
  Number.isInteger(value) && value > 0 ? value : 0
);

export const notifyPendingReviewCountChanged = (eventTarget = window) => {
  eventTarget.dispatchEvent(new Event(PENDING_REVIEW_COUNT_CHANGED_EVENT));
};
