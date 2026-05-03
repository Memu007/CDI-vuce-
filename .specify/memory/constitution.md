<!--
Sync Impact Report:
- Version change: NEW → 1.0.0 (initial constitution)
- Added principles:
  * I. Error-Free User Experience
  * II. Performance Excellence
  * III. Security Without Exposure
  * IV. Accessibility Standards
  * V. Data Integrity
- Added sections:
  * Quality Gates
  * Testing Requirements
- Templates status:
  * plan-template.md ✅ Constitution Check section exists
  * spec-template.md ⚠ Review pending for alignment
  * tasks-template.md ⚠ Review pending for task categorization
- Follow-up TODOs: None - all placeholders filled
-->

# CDI (Carga y Despacho Inteligente) Constitution

## Core Principles

### I. Error-Free User Experience

**Rule**: The system MUST NOT expose critical errors to end users during normal operation flows.

- All user-facing errors MUST be gracefully handled with actionable messages
- Backend exceptions MUST be caught and translated to user-friendly responses
- Failed operations MUST provide clear next steps or recovery options
- Loading states and progress indicators MUST be shown for all async operations
- Form validation MUST occur inline before submission to prevent surprise errors

**Rationale**: Despachantes work under time pressure and cannot afford cryptic errors or system crashes. Every error message must guide them toward resolution, not confusion.

### II. Performance Excellence

**Rule**: All critical user operations MUST complete within 3 seconds under normal load.

- Excel upload and processing: MUST complete < 3sec for files up to 10MB
- PDF extraction with AI: MUST provide feedback within 3sec (may process async)
- Manual form submission: MUST validate and respond < 1sec
- Dashboard loading: MUST render initial view < 2sec
- Excel AVG generation and download: MUST initiate < 2sec

**Performance monitoring**: Response times MUST be logged and monitored. Operations exceeding thresholds trigger warnings.

**Rationale**: Professional despachantes value their time. Slow systems cause frustration and abandonment. The 3-second rule ensures the system feels responsive and professional.

### III. Security Without Exposure

**Rule**: The system MUST NEVER expose secrets, credentials, or sensitive data in logs, errors, or client responses.

- JWT secrets MUST reside only in environment variables
- API keys (Gemini, AFIP) MUST NOT appear in logs or error messages
- User passwords MUST be hashed (never stored plain-text)
- Database credentials MUST be environment-configured only
- CORS MUST restrict origins to explicitly allowed domains
- Rate limiting MUST be active (120 requests/minute default)
- File uploads MUST be size-limited (10MB max) and type-validated

**Compliance check**: Code reviews MUST verify no hardcoded secrets exist.

**Rationale**: Data breach or credential exposure would destroy user trust and potentially expose client commercial data. Security is non-negotiable.

### IV. Accessibility Standards

**Rule**: The system MUST meet WCAG 2.1 Level AA accessibility standards for critical workflows.

- Keyboard navigation MUST work for all interactive elements
- Focus indicators MUST be visible and clear
- Color contrast MUST meet 4.5:1 ratio minimum
- Form inputs MUST have associated labels
- ARIA labels MUST be present for screen readers
- Semantic HTML MUST be used (headings, landmarks, etc.)
- Touch targets MUST be minimum 44x44px for mobile

**Testing requirement**: Automated accessibility audits MUST score > 90/100 on Lighthouse.

**Rationale**: Professional tools must be accessible. Many users may have visual impairments or prefer keyboard navigation. Accessibility is also a legal requirement in many jurisdictions.

### V. Data Integrity

**Rule**: All generated Excel AVG files MUST be 100% compatible with SIM MARIA/MALVINA systems.

- Excel format MUST have exactly 13 columns in specified order
- NCM codes MUST be validated (8-digit format)
- Numeric fields MUST use proper decimal separators
- Required fields MUST never be empty or null
- Data validation MUST occur both client-side and server-side
- Invalid data MUST be filtered out (not silently accepted)
- Generated files MUST be tested against MARIA import process

**Zero-tolerance policy**: No file may be generated that would fail MARIA import.

**Rationale**: The entire purpose of CDI is to produce valid MARIA-compatible files. A file that fails import wastes despachante time and damages trust in the system.

## Quality Gates

### Pre-Release Checklist

Before any release to users, the following MUST be verified:

- [ ] All 5 core principles have been compliance-checked
- [ ] Manual testing of basic and premium flows completed
- [ ] Automated tests pass with > 85% coverage
- [ ] Performance benchmarks meet < 3sec requirement
- [ ] Security scan shows no exposed secrets
- [ ] Accessibility audit scores > 90/100
- [ ] At least 2 real Excel files successfully processed
- [ ] At least 1 real PDF successfully extracted (premium)
- [ ] Generated AVG files tested in MARIA staging environment

### Code Review Requirements

All code changes MUST be reviewed for:

- **Error handling**: Are exceptions caught and user-friendly?
- **Performance**: Any operations that could block > 3sec?
- **Security**: Any logs or responses that expose sensitive data?
- **Accessibility**: New UI elements keyboard-accessible and labeled?
- **Data validation**: Both client and server validation present?

## Testing Requirements

### Test Hierarchy

1. **Unit Tests** (MUST exist for all business logic)
   - Validation functions
   - Excel/PDF parsers
   - JWT utilities
   - NCM lookup logic

2. **Integration Tests** (MUST exist for all API endpoints)
   - Excel upload → processing → download flow
   - PDF upload → extraction → items flow (premium)
   - Manual entry → validation → AVG generation
   - Authentication → authorization flows

3. **E2E Tests** (MUST exist for critical user journeys)
   - Basic user: Login → Upload Excel → Generate AVG → Download
   - Premium user: Login → Upload PDF → Create Client → Generate AVG
   - Error scenarios: Invalid file, network failure, timeout

### Testing Standards

- **Coverage target**: Minimum 80% code coverage
- **Test data**: Use real-world examples from `samples/` directory
- **Performance tests**: Response time assertions for < 3sec rule
- **Accessibility tests**: Automated Lighthouse audits in CI
- **Security tests**: OWASP top 10 basic checks

## Governance

### Amendment Process

This constitution MAY be amended when:

1. New regulatory requirements emerge (e.g., WCAG 2.2, new AFIP standards)
2. User feedback reveals principles that conflict with real-world usage
3. Technical evolution requires principle updates (e.g., new security standards)

**Procedure for amendments**:

1. Proposed change documented with rationale
2. Impact analysis on existing features
3. Approval by project lead
4. Migration plan for affected code
5. Update constitution version (semantic versioning)
6. Communicate changes to all team members

### Versioning Policy

**Version format**: `MAJOR.MINOR.PATCH`

- **MAJOR**: Principle removed or fundamentally redefined (backward incompatible)
- **MINOR**: New principle added or existing principle materially expanded
- **PATCH**: Clarifications, wording improvements, no semantic change

### Compliance Enforcement

- All pull requests MUST include constitution compliance checklist
- Automated tests MUST enforce performance and accessibility thresholds
- Code reviews MUST explicitly verify security and error handling principles
- Quarterly audits MUST review overall system compliance with all 5 principles

**Violation handling**: Any principle violation discovered MUST be:

1. Documented as a high-priority issue
2. Assigned for immediate fix if critical (security, data integrity)
3. Scheduled for fix within 1 sprint if non-critical

---

**Version**: 1.0.0 | **Ratified**: 2025-10-17 | **Last Amended**: 2025-10-17
