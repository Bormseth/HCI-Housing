# Become an RA — Design Sprint 2

This update replaces the empty RA tab with a working Python/NiceGUI application. The dates, expectations, and questions are **sample content**, because the supplied real portal did not have an active RA application. The prototype does not contact UNH or send emails.

## Run it

Use Python 3.10 or newer. Open a terminal in `HCI-Housing`.

```bash
python -m pip install -r requirements.txt
python housing_api.py
```

Keep that terminal running. Open a second terminal in the same folder:

```bash
python housing_ui.py
```

Open **http://127.0.0.1:8085/become-an-ra**. The UI runs on port 8085 and the API on 8006. If you use a virtual environment, activate it in both terminals. The UI does not launch a browser automatically.

## Bring this into your team's existing checkout

Create your own branch in the team's repository before copying files:

```bash
git switch -c feature/become-an-ra
```

Copy these new files and folders from this package:

- `pages/become_an_ra.py`
- `services/ra_rules.py`
- `services/ra_api.py`
- `services/ra_client.py`
- `Media/ra.css`
- `tests/test_ra_api.py`
- `RA_GUIDE.md` and `RA_TESTING.md`

The existing files have small integration changes. If teammates have edited them since this ZIP was made, merge these changes instead of replacing their work:

| File | Change |
| --- | --- |
| `housing_ui.py` | Import `pages.become_an_ra`, remove the old `/become-an-ra` placeholder route, and add the storage secret to `ui.run`. Bind to localhost, disable reload, and leave browser launch manual. |
| `housing_api.py` | Import `router` from `services.ra_api` and call `app.include_router(ra_router)`. Existing housing endpoints stay in place. |
| `components/header.py` | Add optional `active_path` and `compact` arguments. Highlight the current tab and use a shorter header on the RA pages. Existing calls still work. |
| `requirements.txt` | Add `httpx` for asynchronous API requests and `tzdata` for Eastern time on Windows. |
| `.gitignore` | Ignore local draft data, NiceGUI session files, and test caches. |

`RA_UPDATE.patch` contains just the changes made to your supplied files and the new RA files. It is an alternative to copying. From your existing checkout, check it first:

```bash
git apply --check /path/to/RA_UPDATE.patch
git apply /path/to/RA_UPDATE.patch
```

If the check reports conflicts, use the table above to integrate the changes manually. Do not force the patch. The downloadable package excludes Git history and local test data. Keep the `.git` directory in your existing team checkout; do not replace it with a downloaded folder.

Review the changes, commit on your branch, and push that branch for team review. Do not push directly to `main` or force-push.

## What to demonstrate

1. Open **Become an RA**. Explain that the page now answers what the role involves, what to prepare, whether applications are open, and what to do next.
2. Start an application. Click **Continue** with empty fields to demonstrate the error summary and field feedback.
3. Enter sample information, acknowledge the expectations, and continue. Write two responses of 25–200 words.
4. Select **Save & exit**, then **Resume application**. The saved information is restored.
5. Review the automatically generated summary. Use **Edit about you** or **Edit responses** to correct an answer. The review acknowledgment resets when information changes.
6. Confirm the review and submit. Show the confirmation number, timestamp, and read-only submitted answers.

For another demo run, expand **Reset this demo** at the bottom and confirm the reset. This clears only the current browser's sample record.

## How the design addresses the assignment

| Design principle / sprint goal | Implementation | Evidence you can capture |
| --- | --- | --- |
| Visual hierarchy and scale | Smaller portal header; clear page title; application status and primary action near the top; supporting details in smaller type. | Overview screenshot beside the original empty page. |
| Contrast | Navy primary actions, outlined/grouped information, and text-labeled error and success states. Status is communicated with words and icons as well as color. | Start button, an invalid step, and submission confirmation. |
| Gestalt: proximity and common region | Contact fields, expectations, responses, and review information each live in a distinct group. | About you and review screens. |
| Gestalt: similarity | Consistent primary buttons for advancing/submitting and secondary buttons for editing or saving. | The three application steps. |
| Affordances and signifiers | Required-field marks, descriptive buttons, numbered steps, word counts, visible saved status, and an active navigation tab. | A partly completed response and saved draft. |
| Clear flow and feedback | Three steps, actionable validation, save/resume, automatic review, and a confirmation with next steps. | A short end-to-end demo. |
| Python implementation and mock API | NiceGUI renders the UI. FastAPI validates submission and SQLite persists drafts and receipts. | The running UI and the new RA routes in `/docs` on port 8006. |
| Browser testing | Use the checks and participant tasks in `RA_TESTING.md`. | Record actual results and fixes, including problems you discover. |

The RA page was listed as a nice-to-have in the team's assignment notes. This feature is a contribution to that scope; it does not establish that the team's required housing, maintenance, and home-page work is finished.

## Information for the design document

Describe the change as a proposed application workflow, not a reconstruction of UNH's hidden real application. Explain why you chose the sample questions, what assumptions still need checking, and what changed after usability feedback. The existing needfinding report supports simpler organization and clearer information; it does not establish that interviewees specifically requested all of these RA features.

The assignment still asks for paper-prototype/testing evidence, the team's implementation plan, outside-participant testing, a five-minute presentation, and an individual design document covering each part. This code cannot supply those experiences. Add your real observations and photographs; do not describe the automated checks as human usability testing.

If appropriate under your course policy, disclose that ChatGPT/Codex assisted with reviewing the assignment, designing the RA flow, implementing the Python UI and API, and checking functionality. Explain what you personally reviewed, tested, and changed. Check the syllabus for the exact AI-use requirements.

## Local prototype behavior

- Drafts and submissions are stored in `data/ra_applications.sqlite3`. They survive API restarts.
- NiceGUI uses a browser session to find its sample record. Resume in the same browser with its cookies intact. This is not a student login or account system.
- Progress saves on **Continue** and **Save & exit**. Typing alone does not save; the page shows an unsaved-changes message. Use those buttons before leaving or refreshing.
- Concurrent tabs cannot silently overwrite newer saved drafts. Submission retries return the same confirmation. Submitted answers cannot be overwritten.
- API failures leave your current edits on the page and show an actionable message. An initial connection failure shows **Try again**.
- No application data, sessions, or credentials are included in this package. Use fictional information for testing.

Optional environment variables:

| Variable | Purpose |
| --- | --- |
| `RA_APPLICATIONS_OPEN=false` | Set in the API terminal before starting it to demonstrate the closed-cycle state. The sample date does not automatically close the demo. |
| `RA_DB_PATH` | Choose another SQLite file, such as a separate test database. |
| `HOUSING_API_BASE` | Change the RA API URL if port 8006 is unavailable. The existing housing client keeps its original configuration. |
| `STORAGE_SECRET` | Set a stable private session-signing secret for anything beyond a local classroom demo. The default is explicitly for local prototyping. |
| `HOUSING_UI_HOST` | Override the default `127.0.0.1` UI binding if your development environment needs another interface. |

For example, in Windows PowerShell, use `$env:RA_APPLICATIONS_OPEN = "false"` before starting `housing_api.py`. Set it back to `"true"` and restart the API to reopen the demo. Sample content can be changed centrally in `services/ra_rules.py`.

## Automated API checks

With dependencies installed, run:

```bash
python -m unittest discover -s tests -v
```

The tests use a temporary database and cover persistence, isolated browser records, required-field validation, concurrent edits, idempotent submission, submitted-record protection, the closed cycle, demo reset, malformed requests, and existing housing endpoints.
