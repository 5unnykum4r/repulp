# Acme Platform Changelog

## v3.2.1 (December 10, 2025)

*Security patch and bug fixes*

* **Security [SEC-201]:** Fixed XSS vulnerability in user profile bio field. Input is now sanitized server-side before storage and escaped on render.
* **Bugfix [BUG-1847]:** Fixed race condition in concurrent project deletion that could leave orphaned files in object storage.
* **Bugfix [BUG-1852]:** Corrected timezone handling in scheduled report delivery. Reports now respect the organization's configured timezone instead of UTC.
* **Performance [PERF-98]:** Reduced dashboard load time by 40% by implementing Redis caching for aggregated metrics queries.

## v3.2.0 (November 15, 2025)

*New billing features and API improvements*

* **Feature [FEAT-412]:** Added usage-based billing support. Organizations can now configure metered billing for API calls, storage, and compute minutes.
* **Feature [FEAT-415]:** New invoice PDF generation with customizable templates. Supports company logo, custom footer text, and multiple currencies.
* **Feature [FEAT-418]:** Added webhook signature verification using HMAC-SHA256. All outgoing webhooks now include `X-Acme-Signature` header.
* **Improvement [FEAT-420]:** API rate limiting now uses sliding window algorithm instead of fixed window.
* **Deprecation [DEP-15]:** Deprecated XML response format. All endpoints now return JSON only. XML support will be removed in v4.0.

## v3.1.0 (September 20, 2025)

*Project management enhancements*

* **Feature [FEAT-390]:** Project templates: create new projects from predefined templates with pre-configured settings, labels, and workflows.
* **Feature [FEAT-395]:** Bulk user import via CSV upload. Supports up to 10,000 users per import with automatic duplicate detection.
* **Improvement [FEAT-398]:** Improved search indexing. Full-text search now covers file contents, comments, and custom field values. Average query time reduced from 800ms to 120ms.
* **Bugfix [BUG-1790]:** Fixed memory leak in WebSocket connection handler that caused server OOM after approximately 72 hours of continuous operation.

## v3.0.0 (June 1, 2025)

*Major version with breaking changes*

### Breaking Changes

* **[FEAT-350]:** New authentication system using OAuth 2.0 + PKCE. Legacy API keys (v2 format) are no longer accepted. Migrate using the key exchange endpoint before upgrading.
* **[FEAT-355]:** Removed XML response format from all endpoints. Use JSON exclusively.

### New Features

* **[FEAT-360]:** Multi-organization support. Users can belong to multiple organizations and switch between them without re-authenticating.
* **[FEAT-365]:** Audit logging for all administrative actions. Logs are retained for 365 days and exportable in CSV or JSON format.
* **[FEAT-370]:** New permission model with fine-grained roles. Custom roles can be created with specific permission sets per resource type.

## Migration Guide: v2.x to v3.0

| Change          | v2.x Behavior                   | v3.0 Behavior                           | Action Required                                |
| --------------- | ------------------------------- | --------------------------------------- | ---------------------------------------------- |
| Authentication  | Static API key in header        | OAuth 2.0 + PKCE tokens                 | Exchange keys at `/auth/migrate` before cutoff |
| Response format | JSON or XML (via Accept header) | JSON only                               | Remove `Accept: application/xml` from clients  |
| User endpoints  | `/api/v2/users`                 | `/v3/users`                             | Update base URL and remove `/api` prefix       |
| Pagination      | Offset-based (`?page=2`)        | Cursor-based (`?cursor=abc`)            | Switch pagination logic to use cursor tokens   |
| Rate limits     | 500 req/min for all plans       | 1000/min standard, 10000/min enterprise | No action needed (limits increased)            |