  
**TikTok Shop Affiliate AI Engine**

**Requirements & Design Document (Draft)**

*Deterministic, human-in-the-loop pipeline for product research and script writing — self-built scraper, manual filming, manual posting, manual earnings check*

**CONFIDENTIAL — INTERNAL DRAFT**

| Document | TikTok Shop Affiliate AI Engine — Requirements & Design |
| :---- | :---- |
| **Version** | 0.2 (Draft) |
| **Date** | 15 July 2026 |
| **Status** | Draft — for internal use, single-operator project |
| **Owner** | Project Operator / Affiliate Owner |
| **Scope** | TikTok Shop Malaysia — single affiliate account |

# **Table of Contents**

# **1\. Purpose & Scope**

## **1.1 Purpose**

This project removes the repetitive admin work in TikTok Shop affiliate marketing — finding products, researching them, and writing scripts — so the operator can spend their time on filming and posting, which are the two things that actually drive sales and cannot be automated.

The system is built for one person, one TikTok Shop Malaysia affiliate account. It is not a multi-tenant SaaS product at this stage.

## **1.2 In Scope**

* Self-built scraper for live product and market data (own-built, own-hosted, own risk)

* Automated deep research per product (what it does, benefits, USP, review summary)

* Automated script, caption, and hashtag writing in Bahasa Malaysia

* A dashboard with two human approval checkpoints (after research, after script)

* A place to manually log weekly earnings/sales per content card, for feedback

## **1.3 Out of Scope (by decision, not by limitation)**

* Auto-posting to TikTok — posting stays 100% manual, from the operator's phone

* Live automated earnings/commission sync — the operator checks this manually in the TikTok app; the dashboard only stores what is typed in

* Any automated bidding, ad spend, or GMV Max campaign management

* Multi-account or multi-operator support

# **2\. Workflow & Automation Boundaries**

This is the agreed, final workflow. Two manual approval gates were added on top of the original design, and earnings tracking is fully manual by choice.

| Step | Stage | Who | What happens |
| :---- | :---- | :---- | :---- |
| 1 | Product scraping | System | Own scraper pulls live product data (commission %, price, stock, sold count, rating) and shortlists \~5 winning products against set rules. |
| 2 | Deep research | System | For each shortlisted product: what it does, key benefits, USP, and a summary of real customer reviews. |
| 3 | Approval Gate 1 | Operator | Operator reviews the research and approves or rejects each product before any script is written. |
| 4 | Script \+ caption \+ hashtags | System | 3 script angles per approved product, in Malay, plus caption and hashtag set, plus visual shooting notes. |
| 5 | Approval Gate 2 | Operator | Operator picks/edits the preferred script, caption, and hashtags. Nothing moves forward without this. |
| 6 | Filming & editing | Operator | Fully manual. The teleprompter script and shot notes are used as a guide only. |
| 7 | Dashboard update | Operator | Card status is moved to "Ready to Post" once the video is edited. |
| 8 | Posting | Operator | Posted natively from the operator's own phone. No automation touches the TikTok app. |
| 9 | Earnings check | Operator | Operator checks views/sales/commission manually in the TikTok app, then types the numbers into the dashboard against that content card. |

Note: because earnings are entered by hand instead of pulled by API, the "feedback loop" that improves future scripts is only as good and as timely as the operator's habit of logging numbers weekly.

# **3\. System Architecture**

## **3.0 Tech Stack Reference**

| Layer | Technology | Role |
| :---- | :---- | :---- |
| Backend & API | Python (FastAPI) | Orchestrates the 3 stages, serves the dashboard, streams progress. |
| Reasoning Engine | Hermes Agent (Nous Research) | Powers the Research and Script stages only; holds persistent memory of past scripts and results. |
| Tooling Bridge | FastMCP | Wraps the scraper (and optionally the Hermes agents) as callable, portable tools. |
| Scraping Engine | Playwright (Python, async) | Headless browser, intercepts live network responses for product data. |
| Frontend | React (Vite) \+ Tailwind \+ shadcn/ui | Kanban dashboard, approval gates, teleprompter, manual earnings form. |
| Database / Memory | SQLite (Postgres later if needed) | Structured product/script/earnings data, plus the Hermes memory ledger. |

## **3.1 Components**

* Scraper Service — Python \+ Playwright, wrapped as a FastMCP tool, runs headless and on a schedule (cron) or on demand

* Research Agent (Hermes) — built on the Hermes Agent, takes a scraped product, gathers and summarizes product info and reviews into a structured research dossier

* Script Agent (Hermes) — built on the Hermes Agent, takes an approved research dossier plus its own persistent memory of past performance, outputs 3 script variations \+ caption \+ hashtags

* Backend API — FastAPI, exposes REST endpoints to the dashboard, orchestrates the 3 stages in strict sequence, streams progress over SSE/WebSocket

* Database — SQLite for a single-operator setup (Postgres only if this ever needs to run for more than one shop); doubles as the Hermes memory store

* Dashboard — React (Vite) \+ Tailwind, Kanban board, approval buttons, teleprompter view, manual earnings entry form

## **3.2 Why Hermes Agent, and Where It Is Used**

Hermes Agent is used only for the two reasoning stages — Deep Research and Script Writing — because these are the two steps that genuinely need judgement and memory of past results. It is deliberately not used for the scraper (pure code, no reasoning needed) or the dashboard (pure UI). Keeping Hermes scoped to just these two stations keeps the assembly-line design intact: each station still takes a fixed JSON input and returns a fixed JSON output, Hermes is just the engine doing the thinking inside those two boxes.

* Deterministic execution — Hermes runs each request as a single-purpose task, not an open-ended chat, so its output stays close to the required JSON shape.

* Persistent memory — Hermes keeps a local SQLite FTS5 memory ledger of past scripts, hook angles, and the manually-logged performance results tied to them, and can search that memory when writing new scripts.

* Portability — because it is exposed as an MCP-compatible tool, the same Research/Script agent can be called from the FastAPI backend, or tested directly from a workbench like Claude or Cursor during development.

## **3.3 Data Flow (Assembly Line)**

Each stage only talks to the stage next to it, through a fixed JSON shape. No stage calls TikTok directly except the Scraper Service. No stage posts anything to TikTok — that action does not exist in this system at all.

* Scraper Service → writes ScrapedProduct rows to DB

* Research Agent → reads ScrapedProduct, writes ResearchDossier, status \= "Pending Review"

* Operator → approves/rejects in dashboard, status \= "Approved" or "Rejected"

* Script Agent → reads Approved dossiers, writes ScriptVariation options, status \= "Pending Review"

* Operator → picks/edits one variation, status \= "Ready to Film"

* Operator → updates status through Filming → Ready to Post → Posted → Earnings Logged

# **4\. Functional Requirements**

## **4.1 Scraper Module**

* **FR-1.1**  Scraper must search TikTok Shop Malaysia by category/keyword and capture live product data: title, price, commission %, stock, units sold, rating, review count.

* **FR-1.2**  Scraper must intercept the site's internal network responses rather than reading the visible page, so layout changes do not break it as easily.

* **FR-1.3**  Scraper must apply filter rules (minimum commission %, review-quality threshold, minimum stock) and output a shortlist, default size 5\.

* **FR-1.4**  Scraper must save the raw response payload alongside the parsed fields, so a parsing bug does not lose the underlying data.

* **FR-1.5**  Scraper must run on a schedule (e.g. weekly) and also support an on-demand "run now" trigger from the dashboard.

* **FR-1.6**  If zero products pass the filter, the scraper must flag this clearly instead of silently returning nothing.

## **4.2 Deep Research Module (Hermes Agent)**

* **FR-2.1**  For each shortlisted product, generate a research dossier: what the product is/does, 3–5 key benefits, one clear USP, and a short summary of what real reviews say (positive and negative).

* **FR-2.2**  Research must be grounded in data actually pulled for that product (scraped reviews/description), not invented from general knowledge.

* **FR-2.3**  Dossier is written to the dashboard with status "Pending Review" and cannot proceed to scripting without operator approval.

* **FR-2.4**  Operator can reject a dossier with an optional reason; rejected products are archived, not deleted, for later reference.

## **4.3 Script Writing Module (Hermes Agent)**

* **FR-3.1**  Generate exactly 3 script angles per approved product (e.g. Problem Hook, Tech Spec, Aesthetic/Lifestyle), each with hook, body, and CTA in Bahasa Malaysia.

* **FR-3.2**  Generate a caption and a hashtag set for each script angle.

* **FR-3.3**  Generate plain-language visual/shooting notes (what to show, in what order) — not a shot-by-shot camera script.

* **FR-3.4**  Script Agent (Hermes) must query its own SQLite FTS5 memory of past scripts and logged performance before writing, and favor hook styles/angles that performed well before when relevant matches exist.

* **FR-3.5**  Operator can edit any field (hook/body/CTA/caption/hashtags) directly in the dashboard before approving.

* **FR-3.6**  Once approved, the card status changes to "Ready to Film" and the chosen script becomes the single source of truth for that content card.

## **4.4 Dashboard & Workflow Module**

* **FR-4.1**  Kanban-style board with columns matching the workflow: Scraped → Researched (Pending) → Approved → Scripted (Pending) → Approved → Filming → Ready to Post → Posted → Earnings Logged.

* **FR-4.2**  Each card shows product data, research summary, and chosen script at a glance; full detail on click.

* **FR-4.3**  Teleprompter view: large, clean text of the chosen script for use while filming.

* **FR-4.4**  Manual earnings entry form per posted card: views, likes, clicks (if known), units sold, commission earned (MYR), date checked.

* **FR-4.5**  Simple weekly summary view: total commission logged, best-performing product, best-performing script angle — based only on what has been manually entered.

* **FR-4.6**  Basic notification/reminder (in-dashboard, not push) to log earnings for cards posted more than 3 days ago with no entry yet.

# **5\. Non-Functional Requirements**

## **5.1 Reliability**

* Scraper must fail loudly, not silently — a failed run should be visible on the dashboard, not just missing data.

* If a scrape run returns significantly fewer results than usual, flag it for review rather than treating it as a normal empty week.

* Each pipeline stage must be independently re-runnable without corrupting already-approved data from earlier stages.

## **5.2 Scraping Safety (Realistic Expectations)**

* Rotate realistic request timing and use randomized delays between actions — do not hit the site in tight, machine-regular intervals.

* Keep scraping volume low and infrequent (e.g. once a day/week) rather than continuous polling.

* Use a dedicated browser profile/session for scraping, separate from the operator's personal or affiliate login, where possible.

* Log every scrape run (timestamp, result count, errors) so a sudden block or ban is noticed quickly rather than discovered weeks later.

* Accept and document the risk: this scraper reads TikTok's internal, undocumented endpoints. TikTok can change or block this at any time without notice, and this activity may sit outside TikTok's Terms of Service. This is a conscious, accepted business risk for this project, not an oversight.

## **5.3 Data Privacy**

* Store only what is needed for the pipeline to work: product data and review text relevant to the product, not reviewer personal details.

* Manually-entered earnings data is the operator's own business data and stays local to this system.

## **5.4 Performance**

* A full weekly run (scrape → research → script) should complete in minutes, not hours, for a shortlist of \~5 products.

* Dashboard actions (approve/reject/edit) should feel instant — no stage should block the UI while waiting on the AI agents.

## **5.5 Maintainability**

* Scraper selectors/endpoints must be isolated in one config/module, since this is the part most likely to need frequent updates.

* Keep the three stages (scrape, research, script) as independently testable units — each should run and be verified on its own.

# **6\. Data Model (Schema Overview)**

Simplified field list per record — not full code, just what each stage stores.

### **ScrapedProduct**

* product\_id

* title

* price\_rm

* commission\_percentage

* est\_commission\_rm

* review\_score

* stock\_volume

* units\_sold

* product\_url

* scraped\_at

### **ResearchDossier**

* product\_id (link)

* what\_it\_does

* key\_benefits \[list\]

* usp

* review\_summary\_positive

* review\_summary\_negative

* status (Pending / Approved / Rejected)

* rejection\_reason (optional)

### **ScriptVariation**

* product\_id (link)

* angle\_type

* hook\_ms

* body\_ms

* cta\_ms

* caption\_ms

* hashtags \[list\]

* visual\_notes

* is\_selected (boolean)

### **ContentCard**

* card\_id

* product\_id

* selected\_script\_id

* status (Kanban column)

* filmed\_at

* posted\_at

* tiktok\_video\_url (optional, entered manually)

### **EarningsEntry (manual)**

* card\_id (link)

* date\_checked

* views

* likes

* units\_sold

* commission\_earned\_rm

* notes

# **7\. Known Risks & Limitations**

**Platform risk —** The self-built scraper reads TikTok's internal, undocumented endpoints. TikTok can change these anytime, which breaks the scraper without warning, and this kind of automated access may fall outside TikTok's Terms of Service.

**No true "learning" —** The feedback loop is a memory lookup of past scripts and manually-typed results, not a trained model. It will only be as useful as the data the operator actually logs.

**Manual earnings \= delayed feedback —** Because sales data is typed in by hand instead of synced live, the script agent's "what worked before" signal is only as fresh and complete as the operator's logging habit.

**Detection risk —** Headless browser scraping can still be flagged by behavioral anti-bot systems even without visible CAPTCHAs. Lower frequency and randomized timing reduce, but do not remove, this risk.

**Single point of failure —** This is a single-operator, single-account system with no redundancy. If the scraper account/session gets flagged, there is no backup path built in yet.

**Content quality ceiling —** AI-written research and scripts are a starting draft. Both approval gates exist because the operator's judgement, not the AI's, is the actual quality control.

# **8\. Success Metrics**

* Time from "scrape run" to "script approved and ready to film" — target under 30 minutes of operator time per week

* % of scraped products that pass to filming without heavy manual rewrite of the research or script

* Scraper uptime — number of weeks per quarter the scraper runs successfully without needing manual fixes

* Consistency of earnings logging — % of posted cards with an earnings entry within 7 days

# **9\. Phased Roadmap**

### **Phase 1 — Core pipeline (MVP)**

* Scraper Service producing ScrapedProduct records

* Basic dashboard: view scraped products only, no AI research/script yet

* Manual product selection to prove the scraper works reliably first

### **Phase 2 — AI stages**

* Research Agent \+ Approval Gate 1

* Script Agent \+ Approval Gate 2

* Teleprompter view

### **Phase 3 — Feedback loop**

* Manual earnings entry form

* Weekly summary view

* Script Agent starts referencing logged performance

### **Phase 4 — Hardening**

* Scraper monitoring/alerts, retry logic

* Session/timing safeguards

* Review of real-world detection risk after first full month of use

# **10\. Open Questions**

* How often should the scraper run — daily or weekly — given the detection-risk trade-off?

* Should rejected research/scripts feed back into the Script Agent's memory as "what not to do", or just be discarded?

* What is the minimum viable set of earnings fields worth typing in by hand every week, without it becoming a chore the operator skips?

* At what point (if any) would official TikTok Shop Partner API access for the operator's own account replace the manual earnings check?