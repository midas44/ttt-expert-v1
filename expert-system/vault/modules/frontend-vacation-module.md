---
type: module
tags:
  - frontend
  - vacation
  - react
  - redux
  - formik
  - technical-debt
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[modules/frontend-app]]'
  - '[[modules/vacation-service]]'
  - '[[exploration/ui-flows/vacation-pages]]'
branch: release/2.1
---
# Frontend Vacation Module

**Location**: `frontend/frontend-js/src/modules/vacation/`
**Size**: ~27,833 lines across ~377 source files. Separate sick leave module at `modules/sickLeave/` (~3,908 lines).

## Routes

| Route | Page | Permission |
|-------|------|-----------|
| `/vacation/my` | UserVacationsPageContainer | VACATIONS.VIEW |
| `/vacation/request` | RequestVacation | VACATIONS.VIEW_APPROVES |
| `/vacation/chart` | VacationsChartPageContainer | VACATIONS.VIEW |
| `/vacation/payment` | VacationPaymentPageContainer | VACATIONS.VIEW_PAYMENTS |
| `/vacation/days-correction` | CorrectVacationDaysPageContainer | VACATIONS.VIEW_DAYS |
| `/vacation/vacation-days` | VacationDaysPageContainer | VACATIONS.VIEW_EMPLOYEES |
| `/vacation/sick-leaves-of-employees` | SickLeavesOfEmployees | VACATIONS.SICK_LEAVE_VIEW |

## State Management

Redux + Redux-Saga (Ducks pattern). 14 sub-reducers under `state.vacation`: vacations, vacationEvents, vacationChart, vacationPayment, vacationErrorMessage, vacationSpinner, vacationToggles, vacationModals, tableDaysCorrection, tableVacationDays, tableMyVacations, tablePayVacations, tableRequestVacations, myVacation, requestVacation, requestDaysoff, sickLeavesOfEmployees.

Emerging React Query adoption for availability chart only (`useInfiniteQuery` for `/v2/availability-schedule`). Everything else remains Redux-Saga.

## Vacation Create/Edit Form

**Library**: Formik with `enableReinitialize` and `validateOnChange`.

**Fields**: Start date, End date, Payment month, Unpaid checkbox (REGULAR/ADMINISTRATIVE), Vacation days (auto-calculated), Comment, Notify-also (multi-select), Approver (display only), Optional approvers.

**Async interactions during form fill**:
- Period change → `fetchCalendarPeriod` (working days)
- Period change → `GET /v1/paymentdates` (valid payment months)
- Payment month/days change → `GET /v1/vacationdays/available`
- Date selection → `GET /v1/vacations` filtered (shows overlapping absences)

**Submit**: Dispatches `saveCurrentVacation` (create) or `editCurrentVacation` (edit). Saga calls `POST /v1/vacations` or `PUT /v1/vacations/:id`.

## Modal Stack Pattern

Global `ModalManager` reads from `ui/modals` Redux slice — array of `{modalType, modalProps}`. Modal types: CREATE, EDIT, EVENTS, PAYMENT, PAYMENT_SEVERAL, CORRECT_VACATION_DAYS, VACATION_DETAILS, WEEKEND_DETAILS, TRANSFER_DAYSOFF, CONFIRM_DELETE, ERROR. Uses `Symbol()` to discriminate create vs edit.

## API Layer

Three API files:
- **vacationApi.ts**: 16+ endpoints — vacation CRUD, payment dates, approvers, availability chart
- **requestApi.js**: Manager actions — approve, reject, pass, pay
- **daysOffApi.ts**: Day-off CRUD, approvers

## Technical Debt (12 items)

1. **Hooks rules violation**: `useVacationAsyncFields` called inside Formik render prop with eslint-disable
2. **DOM manipulation in React**: Direct `document.querySelector` + `setTimeout(5ms)` for date picker clear
3. **Imperative validation**: `vacationValidationForm` mutates errors via `setErrors()` every render
4. **Typos**: `serUserVacationData` (set), `handleSetCurrentVacationFaysLoading` (Days), `constans.ts` (constants)
5. **Mixed JS/TS**: Core files JS with PropTypes, newer files TS with `any` everywhere
6. **Dual state management**: React Query + Redux-Saga without migration plan
7. **Oversized saga**: `myVacation/sagas.js` = 682 lines, 17 handlers, eslint-disable max-lines
8. **Inconsistent naming**: kebab-case and camelCase duck directories mixed
9. **Split sick leave concern**: Manager-side in vacation module, employee-side in sickLeave module
10. **Legacy patterns**: `connect()` + mapState/mapDispatch throughout, no `useSelector`/`useDispatch`
11. **Payment saga blocking**: `yield take(CONTINUE_PAYMENT)` to wait for user dialog — imperative flow
12. **Hardcoded Confluence link**: Direct URL to vacation regulation docs

See also: [[modules/frontend-app]], [[modules/vacation-service]], [[exploration/ui-flows/vacation-pages]], [[architecture/api-surface]]
