# Pantry Planner — Final Project Presentation (30 minutes)

> Use this as your **slide-by-slide script**. You can paste each section into PowerPoint/Google Slides.
> Team member placeholders: **Member A / B / C / D** (replace with real names).

---

## Slide 1 — Title (0:45)
**Pantry Planner: Smart Meal Planning from What You Already Have**
- Course: [Course Name]
- Team: [Team Name]
- Members: [All members listed]
- Date: [Presentation date]

**Speaker:** Member A

---

## Slide 2 — Agenda (0:45)
1. Product overview, vision, goals
2. Sprint execution summary (1–10)
3. Architecture, detailed design, database, UI/UX
4. DevOps + DevSecOps implementation
5. Demo of implemented user stories (by owners)
6. Lessons learned, challenges, open issues
7. Q&A (one concept question per member)

**Speaker:** Member A

---

## Slide 3 — Product Overview & Problem (1:00)
- Users often have ingredients but don’t know what to cook.
- Existing recipe platforms are overwhelming and not pantry-centric.
- Pantry Planner solves this with ingredient-first recipe discovery.
- Bonus value: grocery planning + bookmarks + admin controls.

**Speaker:** Member A

---

## Slide 4 — Product Vision & Stakeholders (1:00)
**Vision:** Help users reduce food waste and cooking friction by generating meal options from available pantry ingredients.

**Primary stakeholders:**
- End users (home cooks)
- Product owner/team
- Instructor/evaluators

**Success criteria:**
- Faster meal decisions
- Reduced ingredient waste
- Reliable and usable web application

**Speaker:** Member A

---

## Slide 5 — Requirements Summary (1:00)
**Core functional requirements**
- User registration/login/logout
- Ingredient browser and pantry selection
- Recipe discovery from selected ingredients (TheMealDB integration)
- Bookmark recipes
- Grocery list with check/uncheck and print view
- Admin panel for ingredient sync, user management, blacklist

**Non-functional requirements**
- Responsive UI
- Stable CI/testing
- Secure auth/session handling
- Clear documentation and standards

**Speaker:** Member B

---

## Slide 6 — Technology Stack (0:50)
- **Backend:** Python + Flask
- **Database:** SQLite
- **Frontend:** HTML/CSS (Jinja templates)
- **External API:** TheMealDB
- **Dev tools:** GitHub, GitHub Projects, PyTest/unittest, GitHub Actions

**Speaker:** Member B

---

## Slide 7 — Project Goals & Release Plan (1:10)
**Project goals**
- Ingredient-based meal matching
- Pantry and grocery workflow support
- Team-based Scrum delivery across 10 sprints

**Release plan (high level)**
- S1–S3: foundation (auth, DB, initial UI)
- S4–S6: feature expansion (recipes, bookmarks, grocery)
- S7–S8: admin and reliability hardening
- S9–S10: integration, testing, final polish, release

**Speaker:** Member B

---

## Slide 8 — Sprint Execution Snapshot (1:00)
Present a compact timeline:
- Sprint objective
- Delivered scope
- Carry-over items
- Risks/issues resolved

> Add one line per sprint (S1…S10) from your sprint reports.

**Speaker:** Member C

---

## Slide 9 — Team Process & Scrum Practice (1:00)
- Weekly sprint planning and review cadence
- Backlog grooming with priorities
- Ownership assignment per user story
- Daily/regular sync via messages + board updates

**Artifacts to show in repo walkthrough**
- Sprint reports (1–10)
- Planner/Trello export with backlog and sprint tags

**Speaker:** Member C

---

## Slide 10 — Architectural Design (2:00)
**3-layer view**
1. Presentation: Flask templates/pages
2. Application logic: Flask blueprints/routes
3. Data & integrations: SQLite + TheMealDB client

**Key decisions and rationale**
- Flask for speed and simplicity
- SQLite for lightweight deployment
- Blueprint modularization for maintainability

**Speaker:** Member C

---

## Slide 11 — Detailed Design: Modules (1:20)
Show module responsibilities:
- `auth.py`: user auth/session flows
- `pantry.py`: ingredient selection and persistence
- `recipes.py`: recipe search/details/bookmarks
- `grocery.py`: grocery list lifecycle
- `admin.py`: admin management actions
- `integrations/mealdb.py`: external API wrapper

**Speaker:** Member C

---

## Slide 12 — Database Design (1:20)
Add ER-style visual in PPT (tables/relations).

Discuss:
- Users
- Pantry selections
- Bookmarks
- Grocery items
- Ingredient catalog (+ blacklist flags if applicable)

Design rationale:
- Normalized enough for consistency
- Simple schema for fast local setup
- Constraints/indexes for lookups and ownership

**Speaker:** Member D

---

## Slide 13 — UI/UX Design (1:00)
Show screenshots:
- Ingredient browser
- Recipe results/detail
- Grocery list/print
- Admin panel

UX principles used:
- Minimal clicks from ingredient selection → recipe discovery
- Clear authenticated vs anonymous behavior
- Practical utility-first flow for real home usage

**Speaker:** Member D

---

## Slide 14 — Coding & Documentation Standards (0:50)
- Naming conventions, modular structure, route organization
- Pull-request review checklist
- README usage and setup instructions
- Sprint report/document template consistency

**Speaker:** Member D

---

## Slide 15 — Version Management Strategy (0:50)
- GitHub branching (`feature/*`, PR into `main`)
- PR reviews before merge
- Linked issues/project cards
- Traceability from commit → PR → sprint item

**Speaker:** Member A

---

## Slide 16 — Change Management & Bug Tracking (0:50)
- Bug report workflow: reproduce → triage → assign → fix → verify
- Prioritization by severity and sprint goals
- Regression checks before closing

**Speaker:** Member A

---

## Slide 17 — Definition of Ready (Revised) (0:50)
A story is Ready when:
- Clear user value and acceptance criteria defined
- Dependencies identified
- Test approach identified
- Estimation complete and owner assigned

**Speaker:** Member A

---

## Slide 18 — Definition of Done (Revised) (0:50)
A story is Done when:
- Code complete and peer-reviewed
- Tests added/updated and passing
- Integrated with main branch
- Documentation updated
- Demo-ready in deployed/local integrated build

**Speaker:** Member A

---

## Slide 19 — Test Plan & Test Types (1:20)
- Unit tests (route logic, helper functions)
- Integration tests (auth, session, DB interactions)
- Manual UI validation (critical paths)
- Smoke tests before sprint demos

Include:
- What was tested
- How often
- Result summaries and defect trends

**Speaker:** Member B

---

## Slide 20 — Test Automation & CI (1:00)
- Automated test execution via GitHub Actions
- Trigger on push/PR
- Fast feedback for regressions
- Keeps `main` healthy for integrated demo

Show:
- CI workflow screenshot
- Typical pass/fail pipeline view

**Speaker:** Member B

---

## Slide 21 — Development & Deployment Environments (1:00)
**Development**
- Local Python virtual environment
- Flask app + SQLite + seed/sync commands

**Deployment**
- Single-machine integrated run for final release demo
- Optional cloud host notes (DB initialization requirements)

**Speaker:** Member B

---

## Slide 22 — Security Features (1:20)
- Authentication and session-based access control
- Admin-only endpoints guarded by role checks
- Confirmation for destructive admin actions
- Input handling and server-side validation
- Principle of least privilege in feature exposure

**DevSecOps mention:** Security checks integrated into code reviews and testing lifecycle.

**Speaker:** Member D

---

## Slide 23 — DevOps First Way: Flow (1:10)
**Goal:** Fast, smooth flow from idea to user value.

How implemented:
- Sprint slicing into small deliverables
- Branch/PR workflow with frequent merges
- Visual board for work-in-progress control
- CI checks to reduce integration delays

**Speaker:** Member C

---

## Slide 24 — DevOps Second Way: Feedback (1:10)
**Goal:** Amplify and shorten feedback loops.

How implemented:
- PR reviews and comments
- Sprint reviews and demos
- Defect tracking with quick turnaround
- Test results feeding directly into planning

**Speaker:** Member C

---

## Slide 25 — DevOps Third Way: Continuous Learning (1:10)
**Goal:** Create culture of experimentation and improvement.

How implemented:
- Retrospectives each sprint
- Process adjustments (DoR/DoD revisions)
- Root-cause review for recurring defects
- Shared documentation/playbooks

**Speaker:** Member C

---

## Slide 26 — Repo Walkthrough Checklist (1:00)
Show these in GitHub live:
- Team membership
- Product vision
- Goals and release plan
- Sprint reports (1–10)
- Planner/Trello export
- Source code
- Coding/documentation standards
- Environments, version management, tests, automation
- DoR/DoD revisions, architecture/detailed/DB/UI-UX design
- Security and DevOps 3 Ways summary

**Speaker:** Member A

---

## Slide 27 — Demo Plan (Implemented User Stories) (0:50)
**Structure:** each owner demonstrates their stories.

Example split:
- Member A: auth + pantry selection
- Member B: recipe search/detail + bookmarks
- Member C: grocery list flows
- Member D: admin actions + governance features

**Speaker:** Member A (transition slide)

---

## Slide 28 — Live Demo: Member A Stories (1:20)
- Register/login flow
- Ingredient selection behavior
- Session/account behavior differences

**Speaker:** Member A

---

## Slide 29 — Live Demo: Member B Stories (1:20)
- Recipe discovery based on ingredients
- Recipe detail view
- Bookmark add/remove

**Speaker:** Member B

---

## Slide 30 — Live Demo: Member C Stories (1:20)
- Grocery list add/check/remove
- Print-friendly grocery output

**Speaker:** Member C

---

## Slide 31 — Live Demo: Member D Stories (1:20)
- Admin panel access control
- Ingredient sync / user management / blacklist
- Safety prompts for destructive actions

**Speaker:** Member D

---

## Slide 32 — Challenges, Issues, Resolutions (1:00)
- External API reliability/shape changes → resilient integration wrapper + fallback behavior
- Scope balancing across sprints → tighter backlog refinement
- Integration conflicts → disciplined PR + CI + review practice

**Speaker:** Member B

---

## Slide 33 — Lessons Learned (Product + Scrum) (1:10)
**Product development lessons**
- Early user-flow focus improves value delivery.
- Integrate testing earlier to reduce sprint-end stress.

**Scrum lessons**
- Better estimation improved sprint commitment accuracy.
- Stronger DoR/DoD reduced carry-over and ambiguity.

**Speaker:** Member D

---

## Slide 34 — Open Issues / Next Steps (0:50)
- Potential enhancements:
  - Nutritional filtering
  - Smarter ranking/recommendations
  - Multi-user household pantry sharing
  - Better observability/analytics

**Speaker:** Member D

---

## Slide 35 — Q&A Prep: DevOps Third Way + DevSecOps (2:30)
Prepare one question per member. Example practice prompts:

1. **Third Way:** How did your team operationalize continuous learning?
2. **Third Way:** What concrete improvement came from retrospectives?
3. **DevSecOps:** Where were security checks inserted in your pipeline?
4. **DevSecOps:** How did you balance delivery speed with secure coding?

**Suggested answer framework (STAR):**
- Situation
- Task
- Action
- Result

**Speaker:** All members (one answer each)

---

## Slide 36 — Closing (0:30)
- Pantry Planner is fully integrated and demo-ready from one machine.
- Team delivered across 10 sprints with Scrum + DevOps principles.
- Thank you — we welcome your questions.

**Speaker:** Member A

---

# Rubric Coverage Matrix (Use as backup/appendix slide)

| Rubric Area | Where Covered |
|---|---|
| Product overview/vision/requirements/stack | Slides 3–6 |
| Architecture/detailed design rationale | Slides 10–12 |
| Project execution over 10 sprints | Slides 8–9 |
| Lessons (product + Scrum) | Slide 33 |
| Challenges/issues/resolutions | Slide 32 |
| Open issues | Slide 34 |
| DevOps First/Second/Third Way | Slides 23–25 |
| Security features | Slide 22 |
| Implemented user stories demo | Slides 27–31 |
| Q&A per member (Third Way + DevSecOps) | Slide 35 |
| Repo artifacts checklist | Slide 26 |

---

# Presenter Logistics (important)
- Keep strict timing: target 27 minutes content + 3 minutes Q&A buffer.
- Every member speaks in at least 3 sections.
- Have one backup machine and one offline demo path.
- Keep repository open in browser for checklist verification.
- Pre-open app routes before class to reduce dead time.
