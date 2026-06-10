# Holiday Management Design

## Goal

Build an internal holiday-management system for United States and Vietnam locations. The system provides authoritative seed templates, lets ADMIN and HR review company-specific calendars, applies only published holidays to leave calculations, and safely recalculates affected leave requests when calendars change.

The application database remains the source of truth. No runtime dependency on a public holiday API is introduced.

## Confirmed Product Decisions

- Seed all United States federal holidays for 2026 and 2027.
- Seed all Vietnam statutory public holidays for 2026.
- Seeded calendars start as `DRAFT`; an HR or ADMIN must publish them before they affect leave calculations.
- Locations are automatically mapped from `Location.country`, with an ADMIN preview and correction step before drafts are created.
- If every active location in an entity maps to the same country, generate an entity-scoped calendar.
- If an entity contains locations from multiple countries, generate location-scoped calendars.
- When an entity later gains a location from a new country, split future entity-scoped holidays into location-scoped holidays for the existing locations. Preserve past and currently occurring holidays unchanged.
- HR can manage only calendars and holidays belonging to their own entity. ADMIN can manage all calendars, including global holidays.
- Published holidays cannot be edited directly. They must first be unpublished back to Draft.
- Publishing a holiday automatically recalculates affected `PENDING` and `APPROVED` leave requests. Approved requests receive balance refunds for reduced hours.
- Unpublishing requires an impact preview and explicit confirmation. It is blocked if any affected employee lacks enough balance for the additional hours.
- Publish and unpublish operations are atomic and audited.

## Holiday Data Sources And Seed Accuracy

Seed data is maintained as version-controlled application data with a source label and source URL. It is reviewed when introduced and is not silently changed after calendars have been generated.

### United States

The source is the U.S. Office of Personnel Management Federal Holidays schedule. Templates use the official observed dates for typical Monday-Friday federal employees.

#### US 2026

| Date | Holiday |
|---|---|
| 2026-01-01 | New Year's Day |
| 2026-01-19 | Birthday of Martin Luther King, Jr. |
| 2026-02-16 | Washington's Birthday |
| 2026-05-25 | Memorial Day |
| 2026-06-19 | Juneteenth National Independence Day |
| 2026-07-03 | Independence Day, observed |
| 2026-09-07 | Labor Day |
| 2026-10-12 | Columbus Day |
| 2026-11-11 | Veterans Day |
| 2026-11-26 | Thanksgiving Day |
| 2026-12-25 | Christmas Day |

#### US 2027

| Date | Holiday |
|---|---|
| 2027-01-01 | New Year's Day |
| 2027-01-18 | Birthday of Martin Luther King, Jr. |
| 2027-02-15 | Washington's Birthday |
| 2027-05-31 | Memorial Day |
| 2027-06-18 | Juneteenth National Independence Day, observed |
| 2027-07-05 | Independence Day, observed |
| 2027-09-06 | Labor Day |
| 2027-10-11 | Columbus Day |
| 2027-11-11 | Veterans Day |
| 2027-11-25 | Thanksgiving Day |
| 2027-12-24 | Christmas Day, observed |

Source: `https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/`

### Vietnam

The source of statutory entitlement is Article 112 of Vietnam's 2019 Labor Code. The seed represents statutory days off, not every extended government-office closure created by swapping workdays. HR reviews and adjusts the Draft to match the company's approved schedule before publishing.

#### VN 2026

| Date range | Holiday | Seed treatment |
|---|---|---|
| 2026-01-01 | New Year's Day | Statutory |
| 2026-02-16 to 2026-02-20 | Lunar New Year | Five statutory days |
| 2026-04-26 | Hung Kings Commemoration Day | Statutory lunar-calendar date |
| 2026-04-27 | Hung Kings Commemoration Day, compensatory day | Seeded as Draft for HR confirmation because 2026-04-26 is Sunday |
| 2026-04-30 | Reunification Day | Statutory |
| 2026-05-01 | International Labor Day | Statutory |
| 2026-09-01 to 2026-09-02 | National Day | Two statutory days, using the adjacent day before September 2 |

Source reference: Article 112 of Vietnam's 2019 Labor Code and the approved company schedule. Any additional weekend compensation or workday swaps must be confirmed by HR in Draft.

## Domain Model

### HolidayTemplate

An immutable reference calendar for one country and year.

Fields:

- `id`
- `country_code`: `US` or `VN`
- `year`
- `name`
- `source_name`
- `source_url`
- `source_checked_at`
- `version`
- timestamps

Unique constraint: `(country_code, year, version)`.

### HolidayTemplateDate

A reference holiday belonging to a template.

Fields:

- `id`
- `template`
- `holiday_name`
- `start_date`
- `end_date`
- `holiday_type`: `STATUTORY`, `OBSERVED`, or `COMPENSATORY`
- `source_note`

### HolidayCalendar

A company-owned calendar generated from a template or created manually.

Fields:

- `id`
- `name`
- `country_code`
- `year`
- `entity`
- `location`, nullable
- `source_template`, nullable
- `status`: `DRAFT`, `PUBLISHED`, or `ARCHIVED`
- `published_by`, nullable
- `published_at`, nullable
- timestamps

Scope rules:

- ADMIN may create a global calendar where both entity and location are null.
- An entity calendar has `entity` set and `location` null.
- A location calendar has both `entity` and a location belonging to that entity.
- HR cannot create global calendars or calendars for another entity.

Unique constraint prevents multiple active calendars for the same `(year, entity, location, country_code)` scope.

### PublicHoliday Changes

Existing `PublicHoliday` records become calendar-owned company holidays.

Add:

- `calendar`
- `holiday_type`: `STATUTORY`, `OBSERVED`, `COMPENSATORY`, or `COMPANY`
- `status`: `DRAFT`, `PUBLISHED`, or `ARCHIVED`
- `source_note`
- `published_by`, nullable
- `published_at`, nullable

The existing `entity`, `location`, `year`, and date fields remain to minimize disruption to the current leave calculation and calendar-query paths. Their scope must match the parent calendar.

Only `PUBLISHED` holidays are applicable to users. Existing holiday rows are migrated to `PUBLISHED` so current behavior is preserved.

### Auditing

Use the existing `core.AuditLog` model. Extend its choices for:

- entity type `HolidayCalendar` and `PublicHoliday`
- actions `PUBLISH`, `UNPUBLISH`, `GENERATE`, and `SPLIT_SCOPE`

Audit metadata stores before/after state, affected leave IDs, balance deltas, and confirmation actor.

## Country Mapping And Draft Generation

Normalize country values case-insensitively after trimming punctuation and repeated whitespace.

- `US`, `USA`, `United States`, `United States of America` map to `US`.
- `VN`, `Vietnam`, `Viet Nam`, `Việt Nam` map to `VN`.
- Unknown values remain unmapped and appear as warnings.

ADMIN starts generation by selecting a year. The preview endpoint returns:

- available templates for that year
- each entity and location with its normalized country
- proposed entity or location scope
- unknown-country warnings
- existing-calendar conflicts

ADMIN may correct mappings and scope in the preview payload. Confirmation creates calendars and copied holiday rows as Draft. Generation is idempotent and never overwrites an existing calendar.

HR may generate a Draft only from a supported template for their own entity and cannot override the target entity.

## Entity Scope Split

When a new active location makes an entity multi-country:

1. Identify future entity-scoped holidays where `start_date` is after the current local date.
2. Identify the pre-existing active locations that should retain those holidays.
3. Create location-scoped calendars and copied future Draft or Published holidays for those locations.
4. Archive the replaced future entity holidays.
5. Leave past and currently occurring holidays unchanged.
6. Perform the split in one transaction and write a `SPLIT_SCOPE` audit record.

If any target calendar or holiday uniqueness conflict exists, abort the transaction and return an actionable conflict list to ADMIN.

## Permissions

### ADMIN

- List and manage every holiday calendar.
- Preview and generate calendars for any scope.
- Create and manage global holidays.
- Publish and unpublish all calendars.
- Resolve country mappings and scope-split conflicts.

### HR

- List calendars belonging to their own entity.
- Preview and generate templates only for their own entity.
- Create and edit Draft holidays only inside their own entity.
- Publish and unpublish calendars only inside their own entity.
- Cannot create or modify global holidays.

### Other authenticated roles

- Read only the published holidays applicable to themselves through the existing holidays and calendar endpoints.

Permission and scope checks must be enforced in backend services and views, not only in the frontend.

## Lifecycle And Leave Recalculation

### Publish

Before publishing, validate:

- calendar and all contained holidays are Draft
- dates are valid and remain within the calendar year
- location belongs to entity
- no published holiday conflicts exist for the same scope and dates

Within one transaction:

1. Lock the calendar, holidays, affected leave requests, and relevant balances.
2. Compute new hours for affected `PENDING` and `APPROVED` requests.
3. Update request hours.
4. Refund reduced used hours for approved balance-backed requests.
5. Mark calendar and holidays Published.
6. Create notifications for affected employees and current approvers.
7. Write audit records.

If any step fails, roll back the whole publish operation.

### Unpublish Impact Preview

The preview endpoint returns:

- affected Pending and Approved requests
- old and proposed hours per request
- required additional balance per approved request
- users whose balance is insufficient

### Confirm Unpublish

Confirmation requires a preview token tied to the current calendar version so stale previews cannot be accepted.

If any required balance is insufficient, reject without changes. Otherwise, within one transaction:

1. Lock the same records used by publish.
2. Recalculate affected requests without the calendar's holidays.
3. Increase used hours for approved balance-backed requests.
4. Mark calendar and holidays Draft.
5. Notify affected employees and approvers.
6. Write audit records.

## API Surface

Administrative endpoints:

- `GET /api/v1/leaves/holiday-calendars/`
- `POST /api/v1/leaves/holiday-calendars/`
- `GET /api/v1/leaves/holiday-calendars/<id>/`
- `PATCH /api/v1/leaves/holiday-calendars/<id>/`
- `POST /api/v1/leaves/holiday-calendars/generation-preview/`
- `POST /api/v1/leaves/holiday-calendars/generate/`
- `POST /api/v1/leaves/holiday-calendars/<id>/publish/`
- `POST /api/v1/leaves/holiday-calendars/<id>/unpublish-preview/`
- `POST /api/v1/leaves/holiday-calendars/<id>/unpublish/`
- `POST /api/v1/leaves/holiday-calendars/<id>/holidays/`
- `PATCH /api/v1/leaves/holidays/<id>/`
- `DELETE /api/v1/leaves/holidays/<id>/`

Existing employee endpoint remains:

- `GET /api/v1/leaves/holidays/?year=<year>` returns only published holidays applicable to the caller.

Administrative list endpoints support filters for year, country, status, entity, and location.

## Frontend

Add a `Holidays` tab to Settings for ADMIN and HR.

Main screen:

- filters for year, country, status, entity, and location
- calendar cards/table showing scope, source, status, holiday count, and last publish information
- actions: Generate, View/Edit Draft, Publish, Preview Unpublish, Archive

Generation flow:

1. Select year.
2. Review automatic country mapping and proposed scope.
3. Correct unknown mappings or scopes.
4. Confirm creation of Draft calendars.

Calendar editor:

- shows holiday date ranges and types
- supports adding company holidays
- supports editing and deleting only while Draft
- shows source notes and impact warnings

Publish/unpublish dialogs display the affected request and balance summary before confirmation.

The leave-request preview must use the backend-calculated result or a backend preview endpoint so it no longer displays a weekend-only total that disagrees with the saved request.

## Error Handling

- Unknown country mapping: show warning and require correction before generation.
- Existing target calendar: skip creation and report conflict; never overwrite.
- Invalid HR scope: return `403`.
- Editing Published data: return `409` with instruction to unpublish first.
- Stale unpublish preview: return `409` and require a new preview.
- Insufficient balance: return `409` with affected users and required/available hours.
- Scope-split conflict: roll back and return all conflicting calendars/holidays.

## Testing

Backend tests cover:

- exact US 2026, US 2027, and VN 2026 template data
- country alias normalization
- entity-versus-location scope proposals
- ADMIN and HR permissions
- Draft generation idempotency
- Published-only holiday applicability
- publish recalculation and approved balance refunds
- unpublish preview, stale confirmation, insufficient balance blocking, and successful deduction
- transaction rollback on failures
- future entity-scope splitting after a new-country location is added
- employee holiday list and team calendar scope correctness

Frontend tests cover:

- ADMIN and HR tab visibility and filters
- generation preview corrections
- Draft-only editing controls
- publish/unpublish impact dialogs
- backend-aligned leave-hours preview

Manual verification covers:

- an all-US entity
- an all-Vietnam entity
- a mixed-country entity
- an unknown country value
- mobile and desktop Settings layouts

## Out Of Scope

- Runtime synchronization with third-party holiday APIs.
- Automatically generating Vietnam calendars for years without reviewed seed data.
- State-specific United States holidays.
- Employee-specific work schedules other than the existing Monday-Friday calculation.
- Automatically treating government-office workday swaps as company holidays.
