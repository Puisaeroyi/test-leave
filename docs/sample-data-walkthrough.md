# Sample Data Walkthrough - First User Creation

> Demonstrates how data flows through the Leave Management System schema

---

## Step 1: Create Entity (Company)

```sql
INSERT INTO entities (id, name, code, is_active, created_at, updated_at)
VALUES (
    'e1a2b3c4-0000-0000-0000-000000000001',
    'Acme Corporation',
    'ACME',
    true,
    '2026-01-01 00:00:00',
    '2026-01-01 00:00:00'
);
```

**Result:** Company "Acme Corporation" exists in system.

---

## Step 2: Create Locations (Under Entity)

```sql
-- Ho Chi Minh City Office
INSERT INTO locations (id, entity_id, name, city, state, country, timezone, is_active, created_at, updated_at)
VALUES (
    'l1a2b3c4-0000-0000-0000-000000000001',
    'e1a2b3c4-0000-0000-0000-000000000001',  -- Acme Corporation
    'HCMC Headquarters',
    'Ho Chi Minh City',
    NULL,
    'Vietnam',
    'Asia/Ho_Chi_Minh',
    true,
    '2026-01-01 00:00:00',
    '2026-01-01 00:00:00'
);

-- Singapore Office
INSERT INTO locations (id, entity_id, name, city, state, country, timezone, is_active, created_at, updated_at)
VALUES (
    'l1a2b3c4-0000-0000-0000-000000000002',
    'e1a2b3c4-0000-0000-0000-000000000001',  -- Acme Corporation
    'Singapore Branch',
    'Singapore',
    NULL,
    'Singapore',
    'Asia/Singapore',
    true,
    '2026-01-01 00:00:00',
    '2026-01-01 00:00:00'
);
```

**Result:** Acme has 2 locations: HCMC (HQ) and Singapore.

---

## Step 3: Create Departments (Under Entity)

```sql
INSERT INTO departments (id, entity_id, name, code, is_active, created_at, updated_at)
VALUES
(
    'd1a2b3c4-0000-0000-0000-000000000001',
    'e1a2b3c4-0000-0000-0000-000000000001',
    'Engineering',
    'ENG',
    true,
    '2026-01-01 00:00:00',
    '2026-01-01 00:00:00'
),
(
    'd1a2b3c4-0000-0000-0000-000000000002',
    'e1a2b3c4-0000-0000-0000-000000000001',
    'Human Resources',
    'HR',
    true,
    '2026-01-01 00:00:00',
    '2026-01-01 00:00:00'
);
```

**Result:** Acme has Engineering and HR departments.

---

## Step 4: Create Leave Categories (Global)

```sql
INSERT INTO leave_categories (id, name, code, color, requires_document, sort_order, is_active, created_at, updated_at)
VALUES
('c1a2b3c4-0000-0000-0000-000000000001', 'Annual Leave', 'AL', '#4CAF50', false, 1, true, NOW(), NOW()),
('c1a2b3c4-0000-0000-0000-000000000002', 'Sick Leave', 'SL', '#F44336', true, 2, true, NOW(), NOW()),
('c1a2b3c4-0000-0000-0000-000000000003', 'Personal Leave', 'PL', '#2196F3', false, 3, true, NOW(), NOW());
```

**Note:** Categories are for reporting only - all draw from the same 96-hour pool.

---

## Step 5: Create Manager User

**Scenario:** Tran Thi Lan is the Engineering Manager at HCMC.

```sql
-- Manager user (created first or via OAuth)
INSERT INTO users (
    id, email, first_name, last_name,
    oauth_provider, oauth_id,
    role, status,
    entity_id, location_id, department_id,
    join_date, avatar_url, is_active,
    last_login, created_at, updated_at
)
VALUES (
    'u1a2b3c4-0000-0000-0000-000000000099',
    'lan.tran@acme.com',
    'Lan',
    'Tran Thi',
    'google',
    '118234567890123456700',
    'MANAGER',                -- ⭐ MANAGER role
    'ACTIVE',
    'e1a2b3c4-0000-0000-0000-000000000001',  -- Acme
    'l1a2b3c4-0000-0000-0000-000000000001',  -- HCMC HQ
    'd1a2b3c4-0000-0000-0000-000000000001',  -- Engineering
    '2025-01-01',
    'https://lh3.googleusercontent.com/a/manager123',
    true,
    NOW(), NOW(), NOW()
);

-- Create manager's leave balance
INSERT INTO leave_balances (id, user_id, year, allocated_hours, used_hours, adjusted_hours, created_at, updated_at)
VALUES (
    'b1a2b3c4-0000-0000-0000-000000000099',
    'u1a2b3c4-0000-0000-0000-000000000099',
    2026, 96.00, 0.00, 0.00, NOW(), NOW()
);
```

---

## Step 6: Assign Manager to Department + Location

**This is the key step that enables approval authority.**

```sql
-- Link Manager to Engineering department at HCMC location
INSERT INTO department_managers (
    id, department_id, location_id, manager_id, is_active, created_at, updated_at
)
VALUES (
    'dm1a2b3c4-0000-0000-0000-000000000001',
    'd1a2b3c4-0000-0000-0000-000000000001',  -- Engineering
    'l1a2b3c4-0000-0000-0000-000000000001',  -- HCMC HQ
    'u1a2b3c4-0000-0000-0000-000000000099',  -- Lan (Manager)
    true,
    NOW(),
    NOW()
);
```

**Result:** Lan can now approve leave for Engineering employees at HCMC.

```
┌─────────────────────────────────────────────────────────────┐
│ DEPARTMENT_MANAGER Record                                   │
├─────────────────────────────────────────────────────────────┤
│ Department: Engineering                                     │
│ Location:   HCMC Headquarters                               │
│ Manager:    Tran Thi Lan                                    │
│                                                             │
│ ✅ Can approve: Engineering employees at HCMC               │
│ ❌ Cannot approve: Engineering employees at Singapore       │
│ ❌ Cannot approve: HR employees at HCMC                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 7: Employee Login via OAuth

**Scenario:** Nguyen Van Minh logs in with Google for the first time.

```sql
-- User auto-created on first OAuth login (status = ACTIVE, balance auto-created)
INSERT INTO users (
    id, email, first_name, last_name,
    oauth_provider, oauth_id,
    role, status,
    entity_id, location_id, department_id,
    join_date, avatar_url, is_active,
    last_login, created_at, updated_at
)
VALUES (
    'u1a2b3c4-0000-0000-0000-000000000001',
    'minh.nguyen@acme.com',
    'Minh',
    'Nguyen Van',
    'google',
    '118234567890123456789',  -- Google's unique user ID
    'EMPLOYEE',               -- Default role
    'ACTIVE',                 -- ✅ Ready to use immediately!
    'e1a2b3c4-0000-0000-0000-000000000001',  -- Acme (from email domain or selection)
    'l1a2b3c4-0000-0000-0000-000000000001',  -- HCMC HQ
    'd1a2b3c4-0000-0000-0000-000000000001',  -- Engineering
    '2026-01-16',             -- Join date = first login
    'https://lh3.googleusercontent.com/a/photo123',
    true,
    '2026-01-16 09:00:00',
    '2026-01-16 09:00:00',
    '2026-01-16 09:00:00'
);

-- Balance auto-created on first login (96 hours default)
INSERT INTO leave_balances (id, user_id, year, allocated_hours, used_hours, adjusted_hours, created_at, updated_at)
VALUES (
    'b1a2b3c4-0000-0000-0000-000000000001',
    'u1a2b3c4-0000-0000-0000-000000000001',  -- Minh
    2026,
    96.00,   -- Default: 96 hours (12 days × 8h)
    0.00,    -- Nothing used yet
    0.00,    -- No adjustments
    NOW(),
    NOW()
);
```

**User state immediately after login:**
```
┌─────────────────────────────────────────────┐
│ Nguyen Van Minh                             │
│ minh.nguyen@acme.com                        │
├─────────────────────────────────────────────┤
│ Entity:     Acme Corporation                │
│ Location:   HCMC Headquarters               │
│ Department: Engineering                     │
│ Status:     ✅ ACTIVE                       │
├─────────────────────────────────────────────┤
│ Leave Balance (2026):                       │
│   Allocated: 96.00 hours (12 days)          │
│   Used:       0.00 hours                    │
│   Remaining: 96.00 hours (12 days)          │
└─────────────────────────────────────────────┘
```

**User can submit leave requests immediately!**

---

## Step 8: User Submits Leave Request

### Scenario A: Single Day - Full Day (8 hours)

```sql
INSERT INTO leave_requests (
    id, user_id, leave_category_id,
    start_date, end_date,
    shift_type, start_time, end_time,
    total_hours, reason, attachment_url,
    status, approved_by_id, approved_at, rejection_reason, approver_comment,
    created_at, updated_at
)
VALUES (
    'r1a2b3c4-0000-0000-0000-000000000001',
    'u1a2b3c4-0000-0000-0000-000000000001',  -- Minh
    'c1a2b3c4-0000-0000-0000-000000000001',  -- Annual Leave (for reporting)
    '2026-01-20',
    '2026-01-20',  -- Same date = single day
    'FULL_DAY',    -- Full day selected
    NULL,          -- No start_time needed
    NULL,          -- No end_time needed
    8.00,          -- 1 day = 8 hours
    'Family event',
    NULL,
    'PENDING',
    NULL, NULL, NULL, NULL,
    NOW(), NOW()
);
```

### Scenario B: Single Day - Custom Hours (5 hours)

```sql
INSERT INTO leave_requests (
    id, user_id, leave_category_id,
    start_date, end_date,
    shift_type, start_time, end_time,
    total_hours, reason, attachment_url,
    status, approved_by_id, approved_at, rejection_reason, approver_comment,
    created_at, updated_at
)
VALUES (
    'r1a2b3c4-0000-0000-0000-000000000002',
    'u1a2b3c4-0000-0000-0000-000000000001',  -- Minh
    'c1a2b3c4-0000-0000-0000-000000000003',  -- Personal Leave
    '2026-01-22',
    '2026-01-22',    -- Same date = single day
    'CUSTOM_HOURS',  -- Custom hours selected
    '09:00:00',      -- From 9 AM
    '14:00:00',      -- To 2 PM
    5.00,            -- 14:00 - 09:00 = 5 hours
    'Doctor appointment',
    NULL,
    'PENDING',
    NULL, NULL, NULL, NULL,
    NOW(), NOW()
);
```

### Scenario C: Multi-Day (24 hours = 3 days)

```sql
INSERT INTO leave_requests (
    id, user_id, leave_category_id,
    start_date, end_date,
    shift_type, start_time, end_time,
    total_hours, reason, attachment_url,
    status, approved_by_id, approved_at, rejection_reason, approver_comment,
    created_at, updated_at
)
VALUES (
    'r1a2b3c4-0000-0000-0000-000000000003',
    'u1a2b3c4-0000-0000-0000-000000000001',  -- Minh
    'c1a2b3c4-0000-0000-0000-000000000001',  -- Annual Leave
    '2026-02-10',
    '2026-02-12',    -- 3 days (Mon-Wed)
    'FULL_DAY',      -- Multi-day always FULL_DAY
    NULL,
    NULL,
    24.00,           -- 3 days × 8h = 24 hours
    'Lunar New Year travel',
    NULL,
    'PENDING',
    NULL, NULL, NULL, NULL,
    NOW(), NOW()
);
```

---

## Step 9: Manager Approves Request

**First, validate the manager has authority to approve:**

```sql
-- Check if Lan can approve Minh's request
-- Must match: same entity + same location + same department
SELECT dm.manager_id
FROM department_managers dm
JOIN users manager ON dm.manager_id = manager.id
JOIN users employee ON employee.id = 'u1a2b3c4-0000-0000-0000-000000000001'  -- Minh
WHERE dm.department_id = employee.department_id   -- Same department
  AND dm.location_id = employee.location_id       -- Same location
  AND manager.entity_id = employee.entity_id      -- Same entity
  AND dm.manager_id = 'u1a2b3c4-0000-0000-0000-000000000099'  -- Lan
  AND dm.is_active = true;

-- ✅ Returns Lan's ID = She can approve!
```

**Then approve:**

```sql
-- Approve the 3-day request
UPDATE leave_requests SET
    status = 'APPROVED',
    approved_by_id = 'u1a2b3c4-0000-0000-0000-000000000099',  -- Lan (Manager)
    approved_at = NOW(),
    approver_comment = 'Enjoy your holiday!',
    updated_at = NOW()
WHERE id = 'r1a2b3c4-0000-0000-0000-000000000003';

-- Deduct from balance
UPDATE leave_balances SET
    used_hours = used_hours + 24.00,  -- Add 24 hours to used
    updated_at = NOW()
WHERE user_id = 'u1a2b3c4-0000-0000-0000-000000000001'
  AND year = 2026;
```

**Balance after approval:**
```
Allocated: 96.00 hours
Used:      24.00 hours  (+24 from this request)
Adjusted:   0.00 hours
─────────────────────────
Remaining: 72.00 hours (9 days)
```

---

## Step 10: Create Notification

```sql
INSERT INTO notifications (id, user_id, type, title, message, link, is_read, created_at)
VALUES (
    'n1a2b3c4-0000-0000-0000-000000000001',
    'u1a2b3c4-0000-0000-0000-000000000001',  -- Minh (recipient)
    'LEAVE_APPROVED',
    'Leave Request Approved',
    'Your leave request for Feb 10-12 has been approved by your manager.',
    '/leaves/requests/r1a2b3c4-0000-0000-0000-000000000003',
    false,
    NOW()
);
```

---

## Step 11: Audit Log Entry

```sql
INSERT INTO audit_logs (id, user_id, action, entity_type, entity_id, old_values, new_values, ip_address, created_at)
VALUES (
    'a1a2b3c4-0000-0000-0000-000000000001',
    'u1a2b3c4-0000-0000-0000-000000000099',  -- Manager (actor)
    'APPROVE',
    'leave_request',
    'r1a2b3c4-0000-0000-0000-000000000003',
    '{"status": "PENDING"}',
    '{"status": "APPROVED", "approved_by_id": "u1a2b3c4-0000-0000-0000-000000000099"}',
    '192.168.1.100',
    NOW()
);
```

---

## Visual Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA RELATIONSHIPS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ENTITY: Acme Corporation                                                   │
│  ├── LOCATION: HCMC Headquarters (Vietnam)                                  │
│  │   ├── DEPARTMENT_MANAGER: Lan → Engineering @ HCMC ──┐                   │
│  │   └── USER (Employee): Nguyen Van Minh ──────────────┼───┐               │
│  ├── LOCATION: Singapore Branch                         │   │               │
│  ├── DEPARTMENT: Engineering ◄──────────────────────────┘   │               │
│  └── DEPARTMENT: Human Resources                            │               │
│                                                             │               │
│  USER: Tran Thi Lan (MANAGER)                               │               │
│  └── Can approve Engineering @ HCMC ────────────────────────┤               │
│                                                             │               │
│  USER: Nguyen Van Minh (EMPLOYEE) ◄─────────────────────────┘               │
│  ├── LEAVE_BALANCE (2026): 96h allocated, 24h used                          │
│  ├── LEAVE_REQUEST #1: Jan 20 (8h) - PENDING                                │
│  ├── LEAVE_REQUEST #2: Jan 22 (5h, 9AM-2PM) - PENDING                       │
│  └── LEAVE_REQUEST #3: Feb 10-12 (24h) - APPROVED by Lan                    │
│      └── NOTIFICATION: "Leave Approved"                                     │
│      └── AUDIT_LOG: Lan approved request                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Takeaways

| Concept | How It Works |
|---------|--------------|
| **Unified Balance** | All leave types draw from ONE 96-hour pool |
| **Hours not Days** | Everything tracked in hours (1 day = 8 hours) |
| **Single Day Options** | `FULL_DAY` (8h) or `CUSTOM_HOURS` (time range) |
| **Multi-Day** | Auto-calculated as `working_days × 8` |
| **Entity → Location** | Users belong to Entity, assigned to Location |
| **Categories** | For reporting/filtering only, not separate balances |
| **Status Flow** | `ACTIVE` on first login (no waiting) |
| **Approval Authority** | Via `DEPARTMENT_MANAGER`: same entity + location + department |
