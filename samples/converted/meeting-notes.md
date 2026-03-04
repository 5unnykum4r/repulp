# Product Team Standup

**Date:** December 12, 2025 — 10:00 AM PST

**Attendees:** Alex Rivera (PM), Priya Sharma (Engineering Lead),
Marcus Cole (Design), Lin Wei (Backend), Olivia Park (Frontend)

## Sprint 47 Progress

### Completed

* **[PROD-1234] SSO Integration** — Okta and Azure AD now live
  in staging. 14 of 16 test cases passing. Two edge cases remain around token
  refresh when session exceeds 24 hours. Priya assigned to fix by Friday.
* **[PROD-1238] Dashboard Redesign Phase 1** — New layout shipped
  to 10% of users via feature flag. Early metrics show 15% improvement in
  time-to-first-action. Marcus to present full A/B results next Tuesday.
* **[PROD-1241] API Rate Limiting** — Sliding window implementation
  deployed. 429 responses now include `Retry-After` header.

### In Progress

* **[PROD-1245] Bulk Export** — CSV and PDF export working.
  XLSX export blocked on `openpyxl 3.2.x` dependency issue.
  Lin investigating a pin to 3.1.5.
* **[PROD-1247] Mobile Responsive Tables** — Horizontal scroll
  working on iOS Safari. Android Chrome still has a rendering glitch with
  tables wider than 1200px. Targeting next Wednesday.

### Blocked

* **[PROD-1250] Webhook Retry Mechanism** — Waiting on infra
  team to provision the dead-letter queue. Ticket `INFRA-892` filed
  two weeks ago, no update. Alex to escalate.

## Q1 2026 Roadmap

| Priority | Feature                      | Owner           | Target  |
| -------- | ---------------------------- | --------------- | ------- |
| P1       | Real-time collaboration      | Priya           | Feb 14  |
| P1       | SOC 2 audit logging          | Lin             | Jan 31  |
| P1       | Self-serve onboarding flow   | Marcus / Olivia | Mar 15  |
| P2       | Advanced search with filters | Lin             | Mar 31  |
| P2       | Custom report builder        | Olivia          | Mar 31  |
| P2       | Slack integration v2         | TBD             | Mar 31  |
| P3       | Dark mode                    | Marcus          | Stretch |
| P3       | Keyboard shortcuts overhaul  | Olivia          | Stretch |

*Decision:* Team agreed to timebox real-time collaboration to 6 weeks.
If core editing works by Feb 14, we ship. Otherwise, descope to view-only
cursors and push full editing to Q2.

## Technical Debt

| Item                        | Effort  | Impact | Notes                                                                                              |
| --------------------------- | ------- | ------ | -------------------------------------------------------------------------------------------------- |
| Legacy auth module removal  | 3 weeks | High   | Still handles 12% of login traffic via old cookie flow. Can remove after SSO migration in January. |
| Monolithic test suite split | 2 weeks | Medium | CI takes 45 min, should be under 15. Split into unit/integration/e2e with parallel execution.      |
| Reports N+1 query fix       | 1 week  | High   | 200+ queries for 50 rows. Caused a P1 last month (15s page load).                                  |

## Action Items

| Owner  | Action                                      | Due    |
| ------ | ------------------------------------------- | ------ |
| Priya  | Fix SSO token refresh edge cases            | Dec 15 |
| Marcus | Present A/B test results for dashboard      | Dec 17 |
| Lin    | Resolve openpyxl dependency conflict        | Dec 13 |
| Olivia | Fix Android Chrome table rendering          | Dec 18 |
| Alex   | Escalate webhook DLQ ticket with infra      | Dec 12 |
| Alex   | Schedule Q1 roadmap review with leadership  | Dec 19 |
| Priya  | Draft tech debt sprint proposal for January | Dec 20 |

---

*Next standup: December 14, 2025 at 10:00 AM PST*