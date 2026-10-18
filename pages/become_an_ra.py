"""RA overview and a complete three-step NiceGUI application for the class demo."""

import asyncio
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from nicegui import app, ui

from components.header import render_site_header
from services.ra_client import RAClient, RARequestError
from services.ra_rules import CLASS_YEARS, MIN_WORDS, MAX_WORDS, PROMPTS, validate_application, validate_step, word_count

ROOT = "/become-an-ra"
FORM = ROOT + "/apply"
STEPS = ["About you", "Your responses", "Review & submit"]
SAMPLE_NOTICE = "Class prototype · Sample cycle, dates, and expectations. Nothing is sent to UNH."


def heading(text, level=2, css="ra-h2"):
    return ui.label(text).classes(css).props(f'role="heading" aria-level="{level}"')


def primary(text, callback, icon=None):
    return ui.button(text, on_click=callback, icon=icon, color=None).props("unelevated no-caps").classes("ra-primary")


def secondary(text, callback, icon=None):
    return ui.button(text, on_click=callback, icon=icon, color=None).props("flat no-caps").classes("ra-secondary")


def stamp(value):
    if not value:
        return "Not saved yet"
    return datetime.fromisoformat(value).astimezone(ZoneInfo("America/New_York")).strftime("%b %d, %Y at %I:%M %p ET")


def feature(icon, title, copy):
    with ui.row().classes("ra-feature"):
        ui.icon(icon).classes("ra-feature-icon").props('aria-hidden="true"')
        with ui.column():
            heading(title, 3, "ra-h3")
            ui.label(copy).classes("ra-copy")


def timeline(number, title, copy):
    with ui.row().classes("ra-timeline"):
        ui.label(str(number)).classes("ra-timeline-number")
        with ui.column():
            ui.label(title).classes("ra-h3")
            ui.label(copy).classes("ra-small")


def page_shell(application=False):
    render_site_header(active_path=ROOT, compact=True)
    ui.add_head_html("<style>" + (Path(__file__).resolve().parents[1] / "Media" / "ra.css").read_text() + "</style>")
    shell = ui.column().classes("ra-page")
    with shell:
        with ui.element("nav").classes("ra-crumbs").props('aria-label="Breadcrumb"'):
            ui.link("Housing portal", "/")
            ui.label("/").props('aria-hidden="true"')
            if application:
                ui.link("Become an RA", ROOT)
                ui.label("/").props('aria-hidden="true"')
                ui.label("Application")
            else:
                ui.label("Become an RA")
        with ui.row().classes("ra-sample"):
            ui.icon("info_outline", size="18px").props('aria-hidden="true"')
            ui.label(SAMPLE_NOTICE)
    return shell


async def load_data():
    session = app.storage.user.get("ra_session")
    if not session:
        session = str(uuid4())
        app.storage.user["ra_session"] = session
    client = RAClient(session)
    try:
        cycle, record = await asyncio.gather(client.cycle(), client.load())
        return client, cycle, record
    except RARequestError:
        with ui.card().classes("ra-card"):
            heading("The application service is unavailable")
            ui.label("We couldn't load your application. If you already saved a draft, it has not been deleted.").classes("ra-copy")
            ui.label("For this local prototype, start housing_api.py in a separate terminal, then try again.").classes("ra-small")
            primary("Try again", lambda: ui.navigate.reload(), "refresh")
        return None


def footer(client):
    with ui.column().classes("ra-footer"):
        ui.label("Housing & Residential Life · RA application prototype").classes("ra-small")
        with ui.expansion("Reset this demo", icon="restart_alt").classes("w-full text-xs"):
            ui.label("Clear this browser's saved or submitted sample application to start a new test. Other browsers are not affected.").classes("ra-small")

            async def reset():
                try:
                    await client.request("DELETE", "/application")
                    ui.navigate.to(ROOT)
                except RARequestError as error:
                    ui.notify(str(error), type="negative", close_button=True, timeout=0)

            with ui.dialog() as dialog, ui.card().classes("ra-dialog"):
                heading("Reset your sample application?")
                ui.label("This removes your saved answers and confirmation for this demo.").classes("ra-copy")
                with ui.row():
                    secondary("Keep application", dialog.close)
                    primary("Reset application", reset)
            secondary("Reset sample application", dialog.open)


@ui.page(ROOT)
async def ra_overview():
    shell = page_shell()
    with shell:
        result = await load_data()
        if result is None:
            return
        client, cycle, record = result
        with ui.element("div").classes("ra-grid ra-landing-grid"):
            with ui.element("div").classes("ra-stack"):
                with ui.card().classes("ra-card ra-hero"):
                    ui.label("Housing & Residential Life").classes("ra-eyebrow")
                    heading("Become an RA", 1, "ra-title")
                    ui.label("Help make campus feel like home.").classes("text-xl font-semibold")
                    ui.label("Resident Assistants bring people together, connect residents with support, and help build a welcoming place to live.").classes("ra-copy")
                    with ui.row().classes("ra-hero-tags"):
                        for label in ["Community", "Leadership", "Connection"]:
                            ui.label(label).classes("ra-hero-tag")
                with ui.card().classes("ra-card"):
                    heading("Before you apply")
                    ui.label("For this sample application, be ready to confirm that you:").classes("ra-copy")
                    feature("school", "Expect to be enrolled", "You plan to be a student throughout the appointment term.")
                    feature("schedule", "Understand the commitment", "The role includes training, community events, team meetings, and scheduled on-call responsibilities.")
                    with ui.column().classes("ra-hint"):
                        ui.label("Prepare two short responses").classes("ra-h3")
                        ui.label("Why you'd like to be an RA, and how you'd support a resident who feels left out. Each response is 25–200 words.").classes("ra-small")
            with ui.element("div").classes("ra-stack"):
                with ui.card().classes("ra-card ra-status-card"):
                    heading("Your application")
                    status = record["status"]
                    label = {"not_started": "Not started", "draft": "Draft saved", "submitted": "Submitted"}[status]
                    ui.label(label).classes("ra-pill" + (" draft" if status == "draft" else " closed" if status == "not_started" else ""))
                    ui.label(cycle["term"] + " · Sample cycle").classes("ra-h3")
                    ui.label("Applications open" if cycle["open"] else "Applications closed").classes("ra-copy")
                    with ui.column().classes("ra-deadline"):
                        ui.label("SAMPLE DEADLINE").classes("ra-eyebrow")
                        ui.label(cycle["deadline"]).classes("ra-small")
                    if status == "submitted":
                        ui.label(record["confirmation"]).classes("ra-h3")
                        ui.label("Submitted " + stamp(record["submitted_at"])).classes("ra-small")
                        primary("View submitted application", lambda: ui.navigate.to(FORM), "task_alt").classes("ra-full")
                    elif status == "draft":
                        ui.label("Last saved " + stamp(record["saved_at"])).classes("ra-small")
                        primary("Resume application" if cycle["open"] else "View saved draft", lambda: ui.navigate.to(FORM), "arrow_forward").classes("ra-full")
                    elif cycle["open"]:
                        ui.label(cycle["estimate"] + " · 3 steps").classes("ra-small")
                        primary("Start application", lambda: ui.navigate.to(FORM), "arrow_forward").classes("ra-full")
                    else:
                        ui.label("There is no active application. You can still explore the role and prepare your responses for a future cycle.").classes("ra-copy")
                        primary("Applications closed", None).classes("ra-full").disable()
                    if status != "submitted":
                        ui.label("Save your progress and return in this browser.").classes("ra-small")
                with ui.card().classes("ra-card"):
                    heading("How it works")
                    timeline(1, "Apply", "Share your information and two short responses.")
                    timeline(2, "Review", "Check your answers, then submit when you're ready.")
                    timeline(3, "What's next", "See your confirmation and view your submitted application.")
                with ui.column().classes("gap-3 w-full"):
                    heading("Common questions", 2, "ra-h3")
                    for question, answer in [
                        ("Can I finish later?", "Yes. Use Save & exit at any step. Continue also saves your progress. Return in the same browser and choose Resume application."),
                        ("Can I edit my application?", "You can go back and edit before submitting. After submission, your application is read-only. The demo reset clears it if you want another practice run."),
                        ("Are these official RA requirements?", "No. The dates, questions, and expectations are sample content for a class prototype. Check the university's official recruitment information for real requirements."),
                    ]:
                        with ui.expansion(question).classes("ra-faq"):
                            ui.label(answer).classes("ra-small")
        footer(client)


def review_content(data, edit=None):
    with ui.column().classes("ra-review-block"):
        with ui.row().classes("w-full justify-between items-center"):
            heading("About you", 3, "ra-h3")
            if edit:
                secondary("Edit about you", lambda: edit(1), "edit")
        for label, key in [("Full name", "full_name"), ("University email", "email"), ("Class year", "class_year"), ("Major", "major")]:
            with ui.element("div").classes("ra-review-line"):
                ui.label(label).classes("ra-small")
                ui.label(data[key] or "Not provided").classes("ra-review-value")
        ui.label("Enrollment and role expectations acknowledged" if data["enrolled"] and data["expectations"] else "Role acknowledgments incomplete").classes("ra-small")
        ui.element("div").classes("ra-rule")
        with ui.row().classes("w-full justify-between items-center"):
            heading("Your responses", 3, "ra-h3")
            if edit:
                secondary("Edit responses", lambda: edit(2), "edit")
        for key, prompt in PROMPTS.items():
            ui.label(prompt).classes("ra-review-prompt")
            ui.label(data[key] or "Not provided").classes("ra-review-value")
        ui.label("Relevant experience (optional)").classes("ra-review-prompt")
        ui.label(data["experience"] or "Not provided").classes("ra-review-value")


def confirmation(record):
    with ui.card().classes("ra-card ra-success"):
        ui.icon("task_alt").classes("ra-success-icon").props('aria-hidden="true"')
        heading("Application submitted", 1, "ra-title")
        ui.label("You're all set for this sample application.").classes("ra-h3")
        ui.label("Your answers are saved and can be viewed below. This class prototype does not send an application or email to UNH.").classes("ra-copy")
        with ui.column().classes("ra-hint"):
            ui.label("CONFIRMATION NUMBER").classes("ra-eyebrow")
            ui.label(record["confirmation"]).classes("ra-reference")
            ui.label("Submitted " + stamp(record["submitted_at"])).classes("ra-small")
        heading("What happens next?", 2, "ra-h3")
        ui.label("Keep your confirmation number. You can view your submitted answers below. For a real application, follow the university's official recruitment timeline for interviews and decisions.").classes("ra-copy")
        secondary("Return to RA overview", lambda: ui.navigate.to(ROOT), "arrow_back")
    with ui.expansion("View submitted application", icon="description", value=False).classes("ra-faq w-full"):
        review_content(record["data"])


@ui.page(FORM)
async def ra_application():
    shell = page_shell(application=True)
    with shell:
        result = await load_data()
        if result is None:
            return
        client, cycle, record = result
        if record["status"] == "submitted":
            confirmation(record)
            footer(client)
            return
        if not cycle["open"]:
            with ui.card().classes("ra-card"):
                heading("Applications are closed", 1, "ra-title")
                ui.label("You can read your saved draft below. Submission is unavailable for this sample cycle.").classes("ra-copy")
                review_content(record["data"])
                secondary("Return to RA overview", lambda: ui.navigate.to(ROOT))
            footer(client)
            return

        heading("RA application", 1, "ra-title")
        ui.label(cycle["term"] + " · Sample cycle · All fields marked * are required").classes("ra-copy")
        state = {"record": record, "data": dict(record["data"]), "step": record["step"], "dirty": False, "busy": False}
        errors = {}
        fields = {}
        counters = {}

        @ui.refreshable
        def form_view():
            step = state["step"]
            fields.clear()
            counters.clear()
            with ui.card().classes("ra-card"):
                with ui.row().classes("w-full justify-between items-center"):
                    ui.label(f"Step {step} of 3").classes("ra-h3")
                    saved_text = "Unsaved changes · Continue or Save & exit to keep them" if state["dirty"] else "Last saved " + stamp(state["record"]["saved_at"]) if state["record"]["saved_at"] else "Your progress has not been saved yet"
                    saved_label = ui.label(saved_text).classes("ra-saved").props('aria-live="polite"')
                with ui.element("nav").classes("ra-steps").props('aria-label="Application steps"'):
                    for n, name in enumerate(STEPS, start=1):
                        done = n < 3 and not validate_step(state["data"], n)
                        button = ui.button(name, icon="check_circle" if done else f"looks_{['one', 'two', '3'][n-1]}", on_click=lambda n=n: go_to(n), color=None).props("flat no-caps").classes("ra-step" + (" active" if n == step else " done" if done else ""))
                        if n == step:
                            button.props('aria-current="step"')
                        if n > step:
                            button.disable()
            with ui.element("div").classes("ra-grid"):
                with ui.card().classes("ra-card ra-form"):
                    with ui.column().classes("ra-form-heading"):
                        heading(STEPS[step - 1])
                        ui.label({1: "Tell us a little about yourself and review the sample role expectations.", 2: "Use your own examples. Each required response should be 25–200 words.", 3: "Check your information and answers. You can edit either section before submitting."}[step]).classes("ra-copy")
                    error_box = ui.column().classes("ra-error").props('role="alert"')
                    error_box.set_visibility(False)

                    def show_errors(messages):
                        errors.clear()
                        errors.update(messages)
                        error_box.clear()
                        error_box.set_visibility(bool(messages))
                        if messages:
                            with error_box:
                                ui.label("Check these details to continue").classes("font-semibold")
                                for key, message in messages.items():
                                    if key in fields:
                                        ui.button(message, on_click=lambda key=key: fields[key].run_method("focus")).props("flat no-caps")
                                    else:
                                        ui.label(message).classes("text-sm")
                        for field in fields.values():
                            if hasattr(field, "validate"):
                                field.validate()

                    def change(key, value):
                        state["data"][key] = value if value is not None else ""
                        if key != "certify":
                            state["data"]["certify"] = False
                        state["dirty"] = True
                        saved_label.set_text("Unsaved changes · Continue or Save & exit to keep them")
                        errors.pop(key, None)
                        if key in fields and hasattr(fields[key], "validate"):
                            fields[key].validate()
                        if key in counters:
                            count = word_count(value or "")
                            counters[key].set_text(f"{count} / {MAX_WORDS} words · {MIN_WORDS} minimum")
                            counters[key].classes(add="over" if count > MAX_WORDS else "", remove="over" if count <= MAX_WORDS else "")

                    def text_field(key, label, textarea=False, **kwargs):
                        factory = ui.textarea if textarea else ui.input
                        field = factory(label, value=state["data"][key], on_change=lambda e: change(key, e.value), validation=lambda value: errors.get(key), **kwargs).props("outlined").classes("w-full").without_auto_validation()
                        fields[key] = field
                        return field

                    if step == 1:
                        with ui.element("div").classes("ra-fields"):
                            text_field("full_name", "Full name *").props('autocomplete="name" maxlength="120"')
                            text_field("email", "University email *", placeholder="name@unh.edu").props('type="email" autocomplete="email" maxlength="200"')
                            fields["class_year"] = ui.select(CLASS_YEARS, label="Class year *", value=state["data"]["class_year"] or None, on_change=lambda e: change("class_year", e.value), validation=lambda value: errors.get("class_year")).props("outlined").classes("w-full").without_auto_validation()
                            text_field("major", "Major (optional)").props('maxlength="160"')
                        ui.element("div").classes("ra-rule")
                        heading("Sample role expectations", 3, "ra-h3")
                        ui.label("Plan for training, team meetings, community events, and scheduled on-call responsibilities. These are example expectations for the prototype.").classes("ra-copy")
                        with ui.column().classes("ra-checkboxes"):
                            for key, label in [
                                ("enrolled", "I expect to be enrolled throughout the appointment term. *"),
                                ("expectations", "I have read and understand the sample role expectations above. *"),
                            ]:
                                fields[key] = ui.checkbox(label, value=state["data"][key], on_change=lambda e, key=key: change(key, e.value)).props('color="primary"')
                    elif step == 2:
                        for key, prompt in PROMPTS.items():
                            text_field(key, prompt + " *", textarea=True).props('maxlength="8000" autogrow')
                            counters[key] = ui.label(f"{word_count(state['data'][key])} / {MAX_WORDS} words · {MIN_WORDS} minimum").classes("ra-word-count").props('aria-live="polite"')
                        text_field("experience", "Relevant experience (optional)", textarea=True, placeholder="Clubs, jobs, volunteering, or other experiences you would like to share.").props('maxlength="2000"')
                        ui.label("Optional experience: up to 2,000 characters.").classes("ra-small")
                    else:
                        review_content(state["data"], go_to)
                        ui.element("div").classes("ra-rule")
                        with ui.column().classes("ra-checkboxes"):
                            fields["certify"] = ui.checkbox("I have reviewed my answers and confirm that this sample application is ready to submit. *", value=state["data"]["certify"], on_change=lambda e: change("certify", e.value))
                        ui.label("After submitting, your application becomes read-only. Nothing is sent to UNH.").classes("ra-small")

                    action_buttons = []

                    async def save(next_step):
                        new_record = await client.save(state["data"], next_step, state["record"]["version"])
                        state["record"] = new_record
                        state["dirty"] = False
                        saved_label.set_text("Last saved " + stamp(new_record["saved_at"]))

                    async def perform(action):
                        if state["busy"]:
                            return
                        messages = validate_application(state["data"]) if action == "submit" else validate_step(state["data"], step) if action == "continue" else {}
                        show_errors(messages)
                        if messages:
                            first = next((fields[k] for k in messages if k in fields), None)
                            if first is not None:
                                first.run_method("focus")
                            return
                        state["busy"] = True
                        for button in action_buttons:
                            button.disable()
                        try:
                            next_step = min(3, step + 1) if action == "continue" else step
                            await save(next_step)
                            if action == "submit":
                                await client.submit(state["record"]["version"])
                                ui.navigate.to(FORM)
                            elif action == "exit":
                                ui.navigate.to(ROOT)
                            else:
                                state["step"] = next_step
                                form_view.refresh()
                        except RARequestError as error:
                            show_errors({"service": str(error)})
                        finally:
                            state["busy"] = False
                            for button in action_buttons:
                                button.enable()

                    with ui.element("div").classes("ra-actions"):
                        action_buttons.append(secondary("Save & exit", lambda: perform("exit"), "save"))
                        with ui.row().classes("ra-actions-group"):
                            if step > 1:
                                action_buttons.append(secondary("Back", lambda: go_to(step - 1), "arrow_back"))
                            action_buttons.append(primary("Submit application" if step == 3 else "Continue", lambda: perform("submit" if step == 3 else "continue"), "check" if step == 3 else "arrow_forward"))

                with ui.column().classes("ra-stack ra-sticky"):
                    with ui.card().classes("ra-card"):
                        heading("At a glance", 2, "ra-h3")
                        ui.label(cycle["term"] + " · Sample cycle").classes("ra-copy")
                        ui.label("SAMPLE DEADLINE").classes("ra-eyebrow")
                        ui.label(cycle["deadline"]).classes("ra-small")
                        ui.element("div").classes("ra-rule")
                        heading("Your progress is in your hands", 3, "ra-h3")
                        ui.label("Continue saves each completed step. Save & exit saves even an unfinished step, so you can return in this browser.").classes("ra-small")
                    with ui.card().classes("ra-card"):
                        heading({1: "A quick readiness check", 2: "Make your responses specific", 3: "Take one last look"}[step], 2, "ra-h3")
                        ui.label({1: "If you're unsure about the role's time commitment, save a draft and review the overview before continuing.", 2: "Describe what you would do, why you would do it, and how it would support the resident. You don't need previous RA experience to answer these sample questions.", 3: "Check your email and make sure both responses say what you intended. Use Edit to update either section."}[step]).classes("ra-small")
                        ui.label("Use sample information while testing this class prototype.").classes("ra-small")

        def go_to(step):
            if state["busy"]:
                return
            state["step"] = step
            errors.clear()
            form_view.refresh()

        form_view()
        footer(client)
