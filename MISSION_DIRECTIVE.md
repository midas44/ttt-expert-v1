# Mission Directive

## Global Goal

Build comprehensive knowledge base of Time Tracking Tool project (aka TTT aka Time Reporting Tool) and generate
test plans and test cases for all major features. Note that existing documentation can be incomplete / unclear and low-quality, therefore use codebase analysis (static) in combination with application exploration (dynamic) as final truth.

## Project Context

TTT is web application aimed for internal corporate tracking / processing / management of time usage by employees in different domains: 
* reports of hours spent for particular tasks;
* absences of different types: vacations, days-off, sick-leaves.

# Functionality

Different types of time-related data views:
* tables of different entities: reports, vacation requests, project members etc.;
* timecharts of absences (Availability chart);
* statistics view;
With search and filter options to get and display data of interest.

Processing (major areas):
* task addition / renaming;
* report of spent hours (editing / deletion);
* absence request creation / editing / deletion; 
* calculations of working hours: reported vs norm;
* calculations of vacation days: used vs available;
* confirmation and agreement of requests (vacation / day-off);
* confirmation of reported hours;
* accounting operations: periods change (per salary office), vacation payment etc.; 

Administration (major areas):
* projects;
* production calendars / salary offices;
* user's settings / trackers; 

Application UI and features depend on user's role. Roles: employee, contractor, manager, department manager, accountant, admin.

API integrations:
* other internal projects (e.g. Company Staff (aka CS) to get users and salary offices data);
* external trackers (JIRA, GitLab etc.)

Application uses cron jobs to trigger regular operations by time (e.g. syncronization with CS).

There are email notifications of different types.

Note: some features may not mentioned here.

## Priority Areas

1. Absences
2. Reports
3. Accounting
4. Administration

## Information Sources

### Codebase
- **GitLab repo**: https://gitlab.noveogroup.com/noveo-internal-tools/ttt-spring (see skill gitlab-access)
- **Default branch**: release/2.1 (version under development in current sprint)
- **Key branches**: stage (baseline/production version)

### Documentation
- **Confluence space**: see skill confluence-access

  - Key pages:

  All pages in "Time Tracking Tool/Requirements/*"

  e.g:

  https://projects.noveogroup.com/spaces/NOV/pages/130385087/3014+Using+Only+Accrued+Vacation+Days+%D0%98%D1%81%D0%BF%D0%BE%D0%BB%D1%8C%D0%B7%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5+%D1%82%D0%BE%D0%BB%D1%8C%D0%BA%D0%BE+%D0%BD%D0%B0%D0%BA%D0%BE%D0%BF%D0%BB%D0%B5%D0%BD%D0%BD%D1%8B%D1%85+%D0%B4%D0%BD%D0%B5%D0%B9+%D0%BE%D1%82%D0%BF%D1%83%D1%81%D0%BA%D0%B0

  https://projects.noveogroup.com/spaces/NOV/pages/130385089/3092+Advance+Vacation+%D0%92%D0%BE%D0%B7%D0%BC%D0%BE%D0%B6%D0%BD%D0%BE%D1%81%D1%82%D1%8C+%D0%B2%D0%B7%D1%8F%D1%82%D1%8C+%D0%BE%D1%82%D0%BF%D1%83%D1%81%D0%BA%D0%BD%D1%8B%D0%B5+%D0%B0%D0%B2%D0%B0%D0%BD%D1%81%D0%BE%D0%BC

  https://projects.noveogroup.com/spaces/NOV/pages/130387464/Correction+of+vacation+days+%D0%9A%D0%BE%D1%80%D1%80%D0%B5%D0%BA%D1%82%D0%B8%D1%80%D0%BE%D0%B2%D0%BA%D0%B0+%D0%BE%D1%82%D0%BF%D1%83%D1%81%D0%BA%D0%BD%D1%8B%D1%85+%D0%B4%D0%BD%D0%B5%D0%B9

  https://projects.noveogroup.com/spaces/NOV/pages/130385096/%D0%9F%D0%BB%D0%B0%D1%88%D0%BA%D0%B0+%D0%BD%D0%BE%D1%82%D0%B8%D1%84%D0%B8%D0%BA%D0%B0%D1%86%D0%B8%D0%B8+%D0%BE+%D1%80%D0%B5%D0%BF%D0%BE%D1%80%D1%82%D0%B0%D1%85+%D1%81%D0%B2%D1%8B%D1%88%D0%B5+%D0%BD%D0%BE%D1%80%D0%BC%D1%8B

  And some chosen articles beyond Requirements:

  https://projects.noveogroup.com/spaces/NOV/pages/32904541/cron

  https://projects.noveogroup.com/spaces/NOV/pages/110298524/Trackers+integration+setup+and+testing

  - Note: Some pages may be outdated

### Designs
- **Figma project**: see skill figma-access

### Test Management
- **Qase project**: see skill qase-access
  - Note: Can be outdated, unclear, incomplete. Use along with other info sources with descretion

### Tickets
- **GitLab tickets**: https://gitlab.noveogroup.com/noveo-internal-tools/ttt-spring/-/boards (see skill gitlab-access)
  - Key labels: Sprint X, HotFix Sprint X, where X>=11 and X<=15
  - Note: try to define tasks/tickets with latest implementations; but for some areas older tickets can be useful.

### Additional Documents
- **Google Doc**: by links from Confluence pages and GitLab tickets
- **Google Sheet]**: by links from Confluence pages and GitLab tickets

### Testing Environments
Use config/ttt/envs/* to get environment parameters, see skills: playwright-browser, swagger-api, postgres-db
- **Primary dev**: timemachine
- **Secondary dev**: qa-1
- **Primary prod**: stage
- Note: compare dev and prod versions to investigate changes in current Sprint

## Output Requirements
- Test plans as XLSX (one per major module/feature area)
- Test cases as XLSX (detailed, executable)
- Must include description how to generate input test data (by database mining with criteria, random generation in given range, timestamp addition, static values etc.)
- Can include UI, API and DB actions
- Compatible with Google Sheets import
- Note: will be used as input for autotests generation by AI