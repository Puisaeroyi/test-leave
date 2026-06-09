export function ResponsiveRecordRow({ label, children }) {
  return (
    <div className="responsive-record-row">
      <span className="responsive-record-row__label">{label}</span>
      <span className="responsive-record-row__value">{children}</span>
    </div>
  );
}

export default function ResponsiveRecordCard({
  title,
  badge,
  children,
  footer,
  onClick,
  ariaLabel,
}) {
  const interactiveProps = onClick
    ? {
        role: "button",
        tabIndex: 0,
        "aria-label": ariaLabel || `View ${title}`,
        onClick,
        onKeyDown: (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            onClick();
          }
        },
      }
    : {};

  return (
    <article className="responsive-record-card" {...interactiveProps}>
      <div className="responsive-record-card__header">
        <div className="responsive-record-card__title">{title}</div>
        {badge}
      </div>
      <div className="responsive-record-card__body">{children}</div>
      {footer && (
        <div
          className="responsive-record-card__footer"
          onClick={(event) => event.stopPropagation()}
        >
          {footer}
        </div>
      )}
    </article>
  );
}
