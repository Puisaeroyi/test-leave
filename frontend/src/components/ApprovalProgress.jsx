import {
  CheckOutlined,
  ClockCircleOutlined,
  CloseOutlined,
  MinusOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";
import "./ApprovalProgress.css";

const STATUS_META = {
  APPROVED: { label: "Approved", tone: "approved", icon: <CheckOutlined /> },
  REJECTED: { label: "Denied", tone: "rejected", icon: <CloseOutlined /> },
  PENDING: { label: "Pending", tone: "pending", icon: <ClockCircleOutlined /> },
  NOT_REQUIRED: { label: "Not required", tone: "muted", icon: <MinusOutlined /> },
  UNASSIGNED: { label: "Not assigned", tone: "muted", icon: <MinusOutlined /> },
};

export default function ApprovalProgress({ timeline = [], currentStep, actionRequired = false }) {
  if (!timeline.length) return null;

  return (
    <div className="approval-progress" aria-label="Approval progress">
      {timeline.map((step, index) => {
        const meta = STATUS_META[step.status] || STATUS_META.PENDING;
        const isCurrent = step.status === "PENDING" && step.step === currentStep;

        return (
          <div className="approval-progress__segment" key={step.step}>
            <article
              className={[
                "approval-progress__step",
                `approval-progress__step--${meta.tone}`,
                isCurrent ? "approval-progress__step--current" : "",
              ].filter(Boolean).join(" ")}
            >
              <div className="approval-progress__heading">
                <span className="approval-progress__marker">{meta.icon}</span>
                <div>
                  <div className="approval-progress__label">{step.label}</div>
                  <div className="approval-progress__person">
                    {step.approver_name || "No approver assigned"}
                  </div>
                </div>
              </div>

              <div className="approval-progress__meta">
                <span className={`approval-progress__status approval-progress__status--${meta.tone}`}>
                  {isCurrent ? (actionRequired ? "Action required" : "In review") : meta.label}
                </span>
                {step.acted_at && (
                  <time dateTime={step.acted_at}>
                    {dayjs(step.acted_at).format("MMM D, YYYY · HH:mm")}
                  </time>
                )}
              </div>

              {step.note?.trim() && (
                <div className="approval-progress__note">
                  <span>Decision note</span>
                  <p>{step.note}</p>
                </div>
              )}
            </article>

            {index < timeline.length - 1 && (
              <div
                className={[
                  "approval-progress__connector",
                  step.status === "APPROVED" ? "approval-progress__connector--complete" : "",
                ].filter(Boolean).join(" ")}
                aria-hidden="true"
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
