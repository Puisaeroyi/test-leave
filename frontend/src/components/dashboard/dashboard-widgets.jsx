import { Tag } from "antd";

export function MetricCard({ label, value, meta }) {
  return (
    <section className="metric-card">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      {meta && <div className="metric-meta">{meta}</div>}
    </section>
  );
}

export function StatusPill({ status }) {
  const normalized = String(status || "info").toLowerCase();

  return (
    <span className={`status-pill status-pill--${normalized}`}>
      {status || "Info"}
    </span>
  );
}

export function BalanceMeter({ label, remainingHours, allocatedHours, tone = "accent" }) {
  const allocated = Number(allocatedHours) || 0;
  const remaining = Number(remainingHours) || 0;
  const percent = allocated > 0 ? Math.max(0, Math.min(100, (remaining / allocated) * 100)) : 0;
  const fillStyle = tone === "danger"
    ? { background: "linear-gradient(90deg, var(--color-danger), var(--color-warning))" }
    : undefined;

  return (
    <div className="balance-row">
      <div className="balance-row__top">
        <strong>{label}</strong>
        <span className="balance-row__hours">
          {remaining.toFixed(1)}h / {allocated}h
        </span>
      </div>
      <div
        className="balance-meter"
        role="progressbar"
        aria-label={`${label} leave remaining`}
        aria-valuenow={Number(percent.toFixed(0))}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="balance-meter__fill"
          style={{ width: `${percent}%`, ...fillStyle }}
        />
      </div>
    </div>
  );
}

export function EventCard({ event, styleConfig, onClick }) {
  const date = new Date(event.from);

  return (
    <article className="event-card" onClick={onClick}>
      <div className="event-date">
        <span>{date.toLocaleString("en", { month: "short" })}</span>
        <strong>{date.getDate()}</strong>
      </div>
      <div>
        <div className="event-title">{event.title}</div>
        <div className="event-meta">{event.from} → {event.to}</div>
      </div>
      <Tag style={styleConfig.tagStyle}>{styleConfig.label}</Tag>
    </article>
  );
}
