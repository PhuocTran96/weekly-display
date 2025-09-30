# Implementation Plan - New Features

## Overview
This document outlines the implementation plan for three new features:
1. Email Preview Before Sending
2. Processing History & Job Management
3. Advanced Alert Filtering

---

## Feature 1: Email Preview Before Sending

### Backend Tasks

#### Python API Routes (app/routes/process.py)
- [ ] Create `/process/preview-email` endpoint
  - [ ] Load alert data from JSON file
  - [ ] Parse email recipients (PICs and bosses)
  - [ ] Return preview data (recipients, subject, body preview)
  - [ ] Handle errors if alert file not found

#### Email Service (app/services/email_service.py) - NEW FILE
- [ ] Create `EmailService` class
- [ ] Add `get_email_preview()` method
  - [ ] Load contact/alert data
  - [ ] Generate email subject preview
  - [ ] Generate email body preview (HTML/text)
  - [ ] Return list of recipients with store names
- [ ] Add `send_selective_emails()` method
  - [ ] Accept selected recipient list
  - [ ] Send only to selected recipients
  - [ ] Return success/failure for each recipient

### Frontend Tasks

#### Email Preview Modal (templates/components/)
- [ ] Create email preview modal HTML
  - [ ] Recipient list with checkboxes
  - [ ] Email subject display
  - [ ] Email body preview (scrollable)
  - [ ] Select All / Deselect All buttons
  - [ ] Filter by type (PICs / Bosses)
  - [ ] Edit subject line (optional)
  - [ ] Send / Cancel buttons

#### JavaScript Module (static/js/modules/email.module.js)
- [ ] Update `EmailManager` class
- [ ] Add `showEmailPreview()` method
  - [ ] Fetch preview data from API
  - [ ] Display modal with recipients
  - [ ] Populate email preview
- [ ] Add `sendSelectedEmails()` method
  - [ ] Get selected recipients from checkboxes
  - [ ] Send to backend
  - [ ] Show progress/success messages
- [ ] Add modal event listeners
  - [ ] Select/deselect all
  - [ ] Filter recipients
  - [ ] Send button click

#### CSS Styling (static/css/style.css)
- [ ] Add modal overlay styles
- [ ] Add email preview container styles
- [ ] Add recipient list styles with checkboxes
- [ ] Add responsive design for mobile

### Testing
- [ ] Test email preview loads correctly
- [ ] Test recipient selection (all, none, individual)
- [ ] Test filtering by recipient type
- [ ] Test sending to selected recipients only
- [ ] Test error handling (missing alert file)
- [ ] Test mobile responsiveness

---

## Feature 2: Processing History & Job Management

### Backend Tasks

#### Database/Storage
- [ ] Decide on storage method:
  - [ ] Option A: JSON file-based (simple, no DB needed)
  - [ ] Option B: MongoDB (if already using it)
  - [ ] Option C: SQLite (lightweight DB)
- [ ] Create job history storage module

#### Job Storage Service (app/services/job_storage.py) - NEW FILE
- [ ] Create `JobStorage` class
- [ ] Add `save_job()` method
  - [ ] Save job metadata (week, date, files, status)
  - [ ] Store job result data
  - [ ] Store week_num for re-sending emails
- [ ] Add `get_all_jobs()` method
  - [ ] Return all jobs, sorted by date
  - [ ] Support pagination
- [ ] Add `get_job_by_id()` method
- [ ] Add `get_jobs_by_week()` method
- [ ] Add `delete_job()` method
- [ ] Add automatic cleanup (delete jobs older than X days)

#### API Routes (app/routes/history.py) - NEW FILE
- [ ] Create history blueprint
- [ ] Add `/history/` route (list all jobs)
  - [ ] Support query params (page, limit, week)
  - [ ] Return paginated job list
- [ ] Add `/history/<job_id>` route (get job details)
- [ ] Add `/history/<job_id>/resend-emails` route
  - [ ] Validate job exists
  - [ ] Re-trigger email sending for that week
- [ ] Add `/history/<job_id>` DELETE route
  - [ ] Delete job from storage

#### Update Processor (app/services/processor.py)
- [ ] Modify `process_data_background()` to save job on completion
- [ ] Store complete job metadata

### Frontend Tasks

#### History Page (templates/history.html) - NEW FILE
- [ ] Create history page layout
- [ ] Job list table/cards
  - [ ] Week number
  - [ ] Processing date/time
  - [ ] Status (success/failed)
  - [ ] Summary stats (increases/decreases)
  - [ ] Actions (View, Re-send Emails, Delete)
- [ ] Filters
  - [ ] Filter by week number
  - [ ] Filter by date range
  - [ ] Filter by status
- [ ] Pagination controls
- [ ] Search box

#### JavaScript Module (static/js/modules/history.module.js) - NEW FILE
- [ ] Create `HistoryManager` class
- [ ] Add `loadHistory()` method
  - [ ] Fetch from API
  - [ ] Render job list
  - [ ] Handle pagination
- [ ] Add `viewJobDetails()` method
  - [ ] Show modal with full job details
  - [ ] Display all stats and charts
- [ ] Add `resendEmails()` method
  - [ ] Confirm with user
  - [ ] Trigger email resend
  - [ ] Show success/error
- [ ] Add `deleteJob()` method
  - [ ] Confirm with user
  - [ ] Delete via API
  - [ ] Refresh list
- [ ] Add filtering and search

#### Navigation
- [ ] Add "Processing History" link to main nav
- [ ] Update dashboard.html navigation
- [ ] Register history blueprint in app/__init__.py

### Testing
- [ ] Test job saving after processing
- [ ] Test history page loads and displays jobs
- [ ] Test pagination
- [ ] Test filtering by week/date
- [ ] Test viewing job details
- [ ] Test resending emails for old job
- [ ] Test deleting jobs
- [ ] Test automatic cleanup of old jobs

---

## Feature 3: Advanced Alert Filtering

### Backend Tasks

#### Filter Configuration Storage
- [ ] Create filter configuration file/DB schema
- [ ] Define filter structure:
  ```python
  {
    "min_threshold": 5,  # Only alert if change >= 5
    "whitelisted_models": ["Model A", "Model B"],
    "blacklisted_models": ["Test Model"],
    "channels": ["Channel 1", "Channel 2"],  # Only these channels
    "stores": ["Store A", "Store B"]  # Only these stores
  }
  ```

#### Filter Service (app/services/filter_service.py) - NEW FILE
- [ ] Create `FilterService` class
- [ ] Add `load_filters()` method
- [ ] Add `save_filters()` method
- [ ] Add `apply_filters()` method
  - [ ] Filter by threshold
  - [ ] Filter by whitelist/blacklist
  - [ ] Filter by channel/store
  - [ ] Return filtered alert list

#### API Routes (app/routes/filters.py) - NEW FILE
- [ ] Create filters blueprint
- [ ] Add `GET /filters/` route (get current filters)
- [ ] Add `POST /filters/` route (save filters)
- [ ] Add `POST /filters/preview` route
  - [ ] Apply filters to current data
  - [ ] Return count of alerts before/after filtering

#### Update Processor (app/services/processor.py)
- [ ] Add optional filter parameter to processing
- [ ] Apply filters before generating final alerts
- [ ] Store both filtered and unfiltered results

### Frontend Tasks

#### Filter Configuration Page (templates/filters.html) - NEW FILE
- [ ] Create filter configuration form
- [ ] Threshold slider/input
  - [ ] Min increase threshold
  - [ ] Min decrease threshold
- [ ] Model whitelist/blacklist
  - [ ] Search/autocomplete for models
  - [ ] Add/remove models
  - [ ] Toggle whitelist/blacklist mode
- [ ] Channel filter
  - [ ] Multi-select dropdown
- [ ] Store/Dealer filter
  - [ ] Multi-select dropdown
- [ ] Preview section
  - [ ] Show alert count before/after
  - [ ] Show sample filtered results
- [ ] Save/Reset buttons

#### Dashboard Integration
- [ ] Add filter status indicator to dashboard
  - [ ] Show if filters are active
  - [ ] Show filter summary
- [ ] Add "Configure Filters" button
- [ ] Add quick filter toggle (enable/disable)

#### JavaScript Module (static/js/modules/filter.module.js) - NEW FILE
- [ ] Create `FilterManager` class
- [ ] Add `loadFilters()` method
- [ ] Add `saveFilters()` method
- [ ] Add `previewFilters()` method
  - [ ] Show before/after counts
  - [ ] Update preview in real-time
- [ ] Add model search/autocomplete
- [ ] Add form validation

#### Results Page Update
- [ ] Show filter info on results page
  - [ ] Display active filters
  - [ ] Show "X alerts hidden by filters"
- [ ] Add "View All (Ignore Filters)" button

### Testing
- [ ] Test threshold filtering
- [ ] Test whitelist/blacklist models
- [ ] Test channel filtering
- [ ] Test store filtering
- [ ] Test combined filters
- [ ] Test filter preview
- [ ] Test saving/loading filters
- [ ] Test filter toggle (enable/disable)
- [ ] Test filter persistence across sessions

---

## Cross-Feature Tasks

### Documentation
- [ ] Update README.md with new features
- [ ] Add user guide for email preview
- [ ] Add user guide for processing history
- [ ] Add user guide for alert filters
- [ ] Update API documentation

### Configuration
- [ ] Add new config options to config.py
  - [ ] History retention days
  - [ ] Max jobs to keep
  - [ ] Default filter settings
- [ ] Update .env.example with new variables

### Testing & QA
- [ ] Integration testing (all features together)
- [ ] Performance testing (large job history)
- [ ] UI/UX testing
- [ ] Mobile responsiveness testing
- [ ] Cross-browser testing

### Deployment
- [ ] Database migrations (if using DB)
- [ ] Update deployment scripts
- [ ] Backup existing data
- [ ] Test on staging environment
- [ ] Deploy to production

---

## Implementation Priority

### Phase 1: Email Preview (Estimated: 1-2 days)
✅ Highest priority - complements manual email feature
- Backend: Preview endpoint + email service
- Frontend: Modal + recipient selection
- Testing: Basic functionality

### Phase 2: Alert Filtering (Estimated: 1-2 days)
✅ High value - reduces email noise
- Backend: Filter service + API
- Frontend: Filter configuration page
- Integration: Apply to email preview

### Phase 3: Processing History (Estimated: 2-3 days)
✅ Important for auditing and resending
- Backend: Storage + history API
- Frontend: History page
- Integration: Resend emails from history

---

## Notes & Considerations

### Design Decisions to Make:
- [ ] Storage choice for history (JSON/MongoDB/SQLite)?
- [ ] History retention policy (30 days? 90 days?)?
- [ ] Should filters apply retroactively to history?
- [ ] Should email preview show rendered HTML or plain text?

### Optional Enhancements:
- [ ] Email scheduling (send at specific time)
- [ ] Email templates with custom messages
- [ ] Export history to CSV/Excel
- [ ] Advanced statistics on history page
- [ ] Email delivery tracking/status

### Security Considerations:
- [ ] Validate all user inputs
- [ ] Sanitize email content preview
- [ ] Rate limiting on email sending
- [ ] Access control for history deletion
- [ ] Audit log for sensitive operations

---

## Progress Tracking

**Overall Progress: 0%**

- Email Preview: ☐ Not Started
- Processing History: ☐ Not Started
- Alert Filtering: ☐ Not Started

**Last Updated:** 2025-09-30

---

## Questions / Decisions Needed

1. **Storage Method**: Which storage method do you prefer for processing history?
   - JSON files (simple, no dependencies)
   - MongoDB (if already set up)
   - SQLite (lightweight, structured)

2. **History Retention**: How long should we keep processing history?
   - 30 days?
   - 90 days?
   - Forever with manual cleanup?

3. **Email Preview Format**: Should the preview show:
   - Plain text version?
   - Rendered HTML?
   - Both?

4. **Filter Behavior**: Should filters:
   - Apply to all future processing?
   - Be optional per-processing job?
   - Apply retroactively to history?

---

**Please review this plan and:**
- ✏️ Modify any tasks or implementation details
- ✅ Answer the questions in the "Decisions Needed" section
- 🎯 Adjust priorities if needed
- 📝 Add any additional requirements or notes

Once you approve, we'll start implementation! 🚀
