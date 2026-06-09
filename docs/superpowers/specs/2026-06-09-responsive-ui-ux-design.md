# Responsive UI/UX Design

## Goal

Improve the complete Test Leave frontend for mobile, tablet, laptop, and large desktop screens while preserving the current branding, Ant Design component model, business behavior, and API contracts.

## Design Direction

The interface remains a calm, functional office workspace. Existing colors, logo, card language, and navigation model stay recognizable. The improvement focuses on clearer hierarchy, predictable spacing, readable information density, touch-friendly controls, and layouts that adapt to available width instead of merely shrinking.

The differentiation anchor is the existing leave-management dashboard language: compact operational cards, clear status color, and direct action placement. Responsive changes should strengthen that identity rather than introduce decorative panels or a new visual theme.

## Breakpoints

- Mobile: below `768px`.
- Tablet portrait: `768px` through `1023px`.
- Tablet landscape and laptop: `1024px` through `1439px`.
- Large desktop: `1440px` and above.

Breakpoints are CSS-first and aligned with Ant Design's grid behavior. Components may use `Grid.useBreakpoint()` only when markup must change, such as switching an important data table to a mobile card list.

## Application Shell

- Mobile and tablet portrait use the existing navigation Drawer.
- Tablet landscape, laptop, and desktop use the fixed sidebar.
- The header remains sticky and keeps primary actions reachable without horizontal overflow.
- Page content uses fluid gutters and a centered maximum width on large screens.
- Header, sidebar brand, and content spacing use shared tokens rather than page-specific values.
- Mobile viewport height uses modern dynamic viewport units where applicable.

## Shared Responsive Foundation

Shared CSS will define:

- Fluid page padding and section gaps.
- Responsive title sizing and line height.
- Consistent card padding and border radius.
- Toolbars that wrap or stack while keeping the primary action prominent.
- Full-width mobile controls where that improves touch use.
- Modal widths constrained by the viewport with scrollable bodies and reachable actions.
- Responsive `Descriptions` labels and values that do not clip long content.
- Table containers with explicit overflow behavior and sticky or readable action columns where useful.
- Minimum `44px` interactive targets on touch layouts.
- Visible keyboard focus and `prefers-reduced-motion` support.

## Data Presentation

Use a hybrid strategy:

- Important employee workflows become cards below `768px`: leave history, manager leave reviews, business trip history, and business trip reviews.
- Administrative and configuration tables remain tables with deliberate horizontal scrolling: announcements, entities, users, and settings data.
- Tablet and larger screens retain tables unless a specific layout cannot remain readable.
- Mobile cards expose the same meaningful fields and actions as their table row equivalents. Selecting a card opens the same detail flow as selecting a row.
- Status pills, dates, employee identity, and primary actions remain visible without expanding a card.

## Page Behavior

### Dashboard

- Metrics flow from four columns to two and then one or two columns based on width.
- Leave history switches to mobile cards.
- Balance and upcoming events stack naturally below the main history section.
- Sort and new-request actions stack without losing prominence.

### Calendar

- Calendar controls wrap into a compact toolbar.
- Month navigation and primary event action remain visible.
- Calendar cells and event details prioritize legibility over dense desktop presentation on narrow screens.

### Manager And Business Trip Workflows

- Review tables switch to mobile cards.
- Approve and deny actions remain separated and large enough for touch.
- Detail and denial modals use viewport-safe sizing and scrolling.

### Profile, Support, Login, And Password

- Profile identity and descriptions stack cleanly.
- Long email, department, entity, and approver values wrap instead of clipping.
- Authentication cards use narrow-screen gutters and do not depend on fixed widths.
- Support content keeps readable line lengths.

### Settings And Administration

- Settings tabs can scroll horizontally without truncating labels.
- Statistics reflow from multi-column to one or two columns.
- User and entity forms collapse multi-column rows to one column on narrow screens.
- Administrative tables retain horizontal scrolling and accessible row actions.

## Modal And Form Rules

- Modal width is `min(configured width, viewport width minus responsive gutters)`.
- Modal bodies receive a maximum height based on dynamic viewport height and scroll internally.
- Multi-column form rows collapse below the relevant breakpoint.
- Date, time, select, upload, and text controls fill available mobile width.
- Footer actions remain visible, wrap safely, and place the primary action predictably.
- Validation text wraps and remains associated with its field.

## Accessibility

Target WCAG 2.1 AA for the changed interface:

- Maintain sufficient text and control contrast using existing semantic color tokens.
- Preserve semantic headings and button elements.
- Add accessible labels where icon-only controls lack a readable name.
- Ensure keyboard focus is visible.
- Keep focus order consistent when responsive markup changes.
- Avoid color-only status communication by retaining status text.
- Respect reduced-motion preferences.
- Keep touch targets at least `44px` where practical on touch layouts.

## Architecture

The implementation will favor shared CSS and small reusable presentation components over page-specific media-query duplication. A responsive data presentation component may coordinate desktop tables and mobile cards, but existing API calls, row data, and modal state stay in their current pages.

No backend, routing, authentication, notification, approval, or leave-calculation behavior changes are included.

## Validation

- Run ESLint and the Vite production build after changes.
- Verify key widths around `375px`, `768px`, `1024px`, `1366px`, and `1440px`.
- Check navigation, table/card parity, modal scrolling, form submission, keyboard focus, and horizontal overflow.
- Confirm no page creates document-level horizontal scrolling.
- Confirm reduced-motion styles and icon-button accessible names.

## Success Criteria

- Every routed frontend page remains usable without document-level horizontal scrolling at supported widths.
- Primary actions are visible and touch-friendly on mobile.
- Important workflow tables have equivalent mobile card views.
- Administrative tables have intentional contained scrolling.
- Modal content and actions remain reachable on short and narrow screens.
- Existing branding and business behavior remain unchanged.
- Lint and production build pass.
