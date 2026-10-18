# RA prototype testing

## Human usability testing — still to do

The assignment calls for at least **three people who are not on your team**. Automated checks do not meet that requirement. Use fictional information. Ask participants to think aloud; avoid pointing them toward a button unless they are stuck.

Give each person these tasks:

1. You are considering becoming an RA. Find what the role involves and whether you can apply. Tell me what you would prepare.
2. Begin an application. Try moving forward before entering all the required information. Explain what the page asks you to fix.
3. Complete the first step. Start a response, save your work, leave, and return to finish later.
4. Finish both responses. Find and correct a mistake in your name or email from the review step.
5. Submit the sample application. Tell me how you know it worked, whether UNH received anything, and how you would view your submitted answers.

Afterward, ask:

- Was any language confusing or any information missing?
- Did you understand when your work was saved?
- What was the hardest part of the flow?

Use a fresh browser profile or **Reset this demo** between participants. Capture screenshots/photos with permission and avoid recording personal information. Record what actually happens; the table below is intentionally blank.

| Participant | Tasks completed / needed help | Confusing wording or interaction | Observed issue | Fix made / future work |
| --- | --- | --- | --- | --- |
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

## Functional checks

| Check | Expected behavior |
| --- | --- |
| Empty first step | Cannot advance; summary identifies missing details and fields show errors. |
| Invalid email | Cannot advance until a valid email is entered. |
| Short or overlong answer | Word count is visible; advancing is blocked outside 25–200 words. |
| Partial save | Save & exit accepts incomplete drafts; Resume restores the answers and saved step. |
| Refresh after saving | Saved data remains available. Unsaved typing is not promised to persist. |
| Review edit | Summary updates automatically; changing an answer clears the final review acknowledgment. |
| Submit without acknowledgment | Submission is blocked with a clear message. |
| Submit complete application | Confirmation number, timestamp, and read-only submitted answers appear. |
| Revisit submitted application | The same receipt and answers appear. |
| Two browsers | Each browser has its own draft or submission. |
| Two tabs save competing versions | The second save reports a conflict rather than discarding newer work. |
| API unavailable while editing | Error appears and the current edits remain on screen. Retry after restoring the API. |
| Closed sample cycle | Overview explains closure. Saved drafts can be read, and new submission is blocked. |
| Narrow screen | Content stacks; fields and action buttons remain usable; all navigation tabs remain visible in two rows. |
| Keyboard use | Links, fields, checkboxes, and buttons can be reached with Tab; focus is visible. |

## Evidence and demo suggestions

Capture the original placeholder, overview, one validation error, saved/resumed responses, review, and confirmation. Use these to explain what changed and why. A successful technical check is evidence that a function works; participant feedback is evidence about whether the design makes sense to users.

For the five-minute group presentation, keep the RA portion brief enough to leave time for the team's required features. Useful audience questions include: "Was it clear when your progress was saved?" and "What would you need to know about the RA role before starting this application?"

## Development checks completed

The implementation was checked with Python 3.12, NiceGUI 3.18.0, and Chromium. Ten API tests passed. Browser checks covered the overview, required fields, email/response validation, save/resume/reload, review edits and renewed acknowledgment, successful submission, read-only submission, isolated browser records, interrupted API recovery, the closed cycle, and the existing home and housing-application pages. The browser run reported no JavaScript errors.

Desktop rendering was inspected at 1440 pixels wide and phone rendering at 390 pixels wide. These are technical checks performed during development; the participant table above still needs real observations from your usability study.
