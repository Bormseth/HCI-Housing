"""RA pages using the portal's shared header, API client, cards, and stepper."""

import asyncio
from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from nicegui import app, ui

from components.header import render_site_header
from services.api_client import APIError, api_request

ROOT = "/become-an-ra"
FORM = ROOT + "/apply"
STEPS = ["Student Information", "Short Responses", "Review and Submit"]


def heading(text, level=2, classes="text-xl font-bold"):
    return ui.label(text).classes(classes).props(f'role="heading" aria-level="{level}"')


def timestamp(value):
    if not value:
        return "Not saved yet"
    return datetime.fromisoformat(value).astimezone(ZoneInfo("America/New_York")).strftime("%b %d, %Y at %I:%M %p ET")


def prototype_note():
    ui.label("Class prototype. Dates and expectations are examples; nothing is sent to UNH.").classes("text-xs text-gray-500")


async def load_application():
    session = app.storage.user.get("ra_session")
    if not session:
        session = str(uuid4())
        app.storage.user["ra_session"] = session

    async def request(method, path, data=None):
        return await api_request(method, "/ra" + path, data, session=session)

    try:
        cycle, record = await asyncio.gather(request("GET", "/cycle"), request("GET", "/application"))
        return request, cycle, record
    except APIError:
        with ui.card().classes("w-full p-6 rounded-xl shadow-sm"):
            heading("Application service unavailable")
            ui.label("Your saved application has not been deleted. Start the API and try again.").classes("text-gray-600")
            ui.button("Try again", icon="refresh", on_click=ui.navigate.reload)
        return None


def reset_demo(request):
    async def reset():
        try:
            await request("DELETE", "/application")
            ui.navigate.to(ROOT)
        except APIError as error:
            ui.notify(str(error), type="negative", close_button=True)

    with ui.dialog() as dialog, ui.card().classes("p-6 gap-4"):
        heading("Reset this sample application?")
        ui.label("Your saved answers and confirmation will be cleared for this browser.")
        with ui.row():
            ui.button("Keep application", on_click=dialog.close).props("flat")
            ui.button("Reset application", on_click=reset)
    ui.button("Reset demo", icon="restart_alt", on_click=dialog.open).props("flat dense color=grey-7")


@ui.page(ROOT)
async def ra_overview():
    render_site_header(active_path=ROOT)
    with ui.column().classes("application-content"):
        result = await load_application()
        if result is None:
            return
        request, cycle, record = result
        heading("Become an RA", 1, "text-3xl font-bold")
        with ui.row().classes("application-banner items-center no-wrap"):
            ui.icon("people_outline", size="22px").props('aria-hidden="true"')
            ui.label("Help make campus feel like home. Support your community as a Resident Assistant.").classes("text-sm")
        prototype_note()
        with ui.element("div").classes("application-grid"):
            with ui.card().classes("w-full p-6 rounded-xl shadow-sm"):
                status = record["status"]
                with ui.row().classes("w-full justify-between items-center"):
                    heading(cycle["term"])
                    if status == "submitted":
                        ui.badge("Submitted", color="positive")
                    elif status == "draft":
                        ui.badge("Draft saved", color="primary")
                    else:
                        ui.badge("Available" if cycle["open"] else "Closed", color="positive" if cycle["open"] else "grey")
                ui.label("Resident Assistant application").classes("text-gray-600")
                ui.label("Sample deadline: " + cycle["deadline"]).classes("text-sm text-gray-600")
                if status == "submitted":
                    ui.label(record["confirmation"]).classes("font-semibold")
                    ui.label("Submitted " + timestamp(record["submitted_at"])).classes("text-sm text-gray-600")
                    ui.button("View Application", icon="description", on_click=lambda: ui.navigate.to(FORM)).classes("mt-4")
                elif status == "draft":
                    ui.label("Last saved " + timestamp(record["saved_at"])).classes("text-sm text-gray-600")
                    if not cycle["open"]:
                        ui.label("Applications are closed. Your saved draft is still available.").classes("text-sm text-gray-600")
                    ui.button("Resume Application" if cycle["open"] else "View Saved Draft", icon="arrow_forward", on_click=lambda: ui.navigate.to(FORM)).classes("mt-4")
                elif cycle["open"]:
                    ui.label("3 steps · " + cycle["estimate"]).classes("text-sm text-gray-600")
                    ui.button("Start Application", icon="arrow_forward", on_click=lambda: ui.navigate.to(FORM)).classes("mt-4")
                else:
                    ui.label("There is no active application for this sample cycle.").classes("text-gray-600")
                    ui.button("Applications Closed").classes("mt-4").disable()
            with ui.card().classes("w-full p-6 rounded-xl shadow-sm"):
                heading("Before you apply")
                ui.label("Confirm enrollment and review the training, meeting, and on-call commitments.").classes("text-gray-600")
                ui.label("Prepare two short responses: why you want to be an RA, and how you would help a resident who feels left out.").classes("text-gray-600")
                ui.label(f"Each response: {cycle['min_words']}–{cycle['max_words']} words.").classes("text-sm text-gray-600")
                ui.label("Use Save & exit to finish later in the same browser.").classes("text-sm text-gray-600")
        reset_demo(request)


def review_answers(data, prompts, edit=None):
    with ui.column().classes("w-full gap-3"):
        with ui.row().classes("w-full justify-between items-center"):
            heading("Student information", 3, "text-lg font-semibold")
            if edit:
                ui.button("Edit information", icon="edit", on_click=lambda: edit(1)).props("flat dense")
        for label, key in [("Name", "full_name"), ("Email", "email"), ("Class year", "class_year"), ("Major", "major")]:
            ui.label(f"{label}: {data[key] or 'Not provided'}").classes("application-answer")
        ui.separator()
        with ui.row().classes("w-full justify-between items-center"):
            heading("Short responses", 3, "text-lg font-semibold")
            if edit:
                ui.button("Edit responses", icon="edit", on_click=lambda: edit(2)).props("flat dense")
        for key, prompt in prompts.items():
            ui.label(prompt).classes("font-semibold")
            ui.label(data[key] or "Not provided").classes("application-answer")
        if data["experience"]:
            ui.label("Relevant experience").classes("font-semibold")
            ui.label(data["experience"]).classes("application-answer")


def submitted_application(request, cycle, record):
    with ui.card().classes("w-full p-6 rounded-xl shadow-sm gap-4"):
        with ui.row().classes("items-center"):
            ui.icon("check_circle", color="positive")
            heading("Application submitted")
        ui.label("Confirmation: " + record["confirmation"]).classes("font-semibold")
        ui.label("Submitted " + timestamp(record["submitted_at"])).classes("text-gray-600")
        ui.label("Your submitted answers are saved below. Nothing is sent to UNH.").classes("text-gray-600")
        with ui.expansion("View submitted application", icon="description").classes("w-full"):
            review_answers(record["data"], cycle["prompts"])
        ui.button("Return to RA overview", icon="arrow_back", on_click=lambda: ui.navigate.to(ROOT))
    reset_demo(request)


@ui.page(FORM)
async def ra_application():
    render_site_header(active_path=ROOT)
    with ui.column().classes("application-content application-form"):
        result = await load_application()
        if result is None:
            return
        request, cycle, record = result
        ui.button("Become an RA", icon="arrow_back", on_click=lambda: ui.navigate.to(ROOT)).props("flat")
        heading(cycle["term"] + " RA Application", 1, "text-3xl font-bold")
        prototype_note()
        if record["status"] == "submitted":
            submitted_application(request, cycle, record)
            return
        if not cycle["open"]:
            with ui.card().classes("w-full p-6 rounded-xl shadow-sm"):
                heading("Applications are closed")
                ui.label("You can view your saved draft, but submission is unavailable.").classes("text-gray-600")
                review_answers(record["data"], cycle["prompts"])
            reset_demo(request)
            return

        ui.label("Complete the three steps below. Fields marked * are required.").classes("text-gray-600")
        data = dict(record["data"])
        state = {"record": record, "step": record["step"], "busy": False}
        fields, errors, error_boxes, counters = {}, {}, {}, {}
        actions = []
        saved = ui.label("Last saved " + timestamp(record["saved_at"]) if record["saved_at"] else "Use Next or Save & exit to save your progress.").classes("text-sm text-gray-600").props('aria-live="polite"')

        def change(key, value):
            data[key] = value if value is not None else ""
            if key != "certify":
                data["certify"] = False
                if "certify" in fields:
                    fields["certify"].set_value(False)
            saved.set_text("Unsaved changes · Use Next or Save & exit to keep them.")
            errors.pop(key, None)
            if key in fields and hasattr(fields[key], "validate"):
                fields[key].validate()
            if key in counters:
                count = len((value or "").split())
                counters[key].set_text(f"{count}/{cycle['max_words']} words · {cycle['min_words']} minimum")
                counters[key].classes(add="text-red-700" if count > cycle["max_words"] else "", remove="text-red-700" if count <= cycle["max_words"] else "")

        def input_field(key, label, textarea=False, **kwargs):
            factory = ui.textarea if textarea else ui.input
            field = factory(label, value=data[key], on_change=lambda e: change(key, e.value), validation=lambda value: errors.get(key), **kwargs).classes("w-full").without_auto_validation()
            fields[key] = field
            return field

        def show_error(number, error):
            errors.clear()
            errors.update(error.errors)
            box = error_boxes[number]
            box.clear()
            box.set_visibility(True)
            with box:
                ui.label(str(error)).classes("font-semibold")
                for message in error.errors.values():
                    ui.label(message).classes("text-sm")
            for field in fields.values():
                if hasattr(field, "validate"):
                    field.validate()
            first = next((fields[key] for key in error.errors if key in fields), None)
            if first is not None:
                first.run_method("focus")

        def go_to(number):
            if state["busy"]:
                return
            state["step"] = number
            stepper.set_value(STEPS[number - 1])

        async def act(action, number):
            if state["busy"]:
                return
            state["busy"] = True
            for element in [*actions, *fields.values()]:
                element.disable()
            target = min(number + 1, 3) if action == "next" else number
            payload = {"data": dict(data), "step": target, "expected_version": state["record"]["version"]}
            if action != "exit":
                payload["validate_step"] = number
            try:
                result = await request("PUT", "/application", payload)
                state["record"] = result
                saved.set_text("Last saved " + timestamp(result["saved_at"]))
                errors.clear()
                for box in error_boxes.values():
                    box.set_visibility(False)
                for field in fields.values():
                    if hasattr(field, "validate"):
                        field.validate()
                if action == "submit":
                    await request("POST", "/application/submit", {"expected_version": result["version"]})
                    ui.navigate.to(FORM)
                elif action == "exit":
                    ui.navigate.to(ROOT)
                else:
                    review.refresh()
                    state["step"] = target
                    stepper.set_value(STEPS[target - 1])
            except APIError as error:
                show_error(number, error)
            finally:
                state["busy"] = False
                for element in [*actions, *fields.values()]:
                    element.enable()

        @ui.refreshable
        def review():
            review_answers(data, cycle["prompts"], go_to)

        with ui.stepper(value=STEPS[record["step"] - 1]).classes("w-full application-stepper") as stepper:
            for number, title in enumerate(STEPS, start=1):
                with ui.step(title):
                    error_boxes[number] = ui.column().classes("application-errors").props('role="alert"')
                    error_boxes[number].set_visibility(False)
                    if number == 1:
                        ui.label("Enter your information and review the sample role expectations.").classes("text-gray-600")
                        input_field("full_name", "Full name *").props('autocomplete="name" maxlength="120"')
                        input_field("email", "University email *", placeholder="name@unh.edu").props('type="email" autocomplete="email" maxlength="200"')
                        fields["class_year"] = ui.select(cycle["class_years"], label="Class year *", value=data["class_year"] or None, on_change=lambda e: change("class_year", e.value), validation=lambda value: errors.get("class_year")).classes("w-full").without_auto_validation()
                        input_field("major", "Major (optional)").props('maxlength="160"')
                        heading("Sample role expectations", 3, "text-lg font-semibold")
                        ui.label("The role includes training, meetings, community events, and scheduled on-call responsibilities.").classes("text-gray-600")
                        for key, label in [
                            ("enrolled", "I expect to be enrolled throughout the appointment term. *"),
                            ("expectations", "I have read and understand the sample role expectations above. *"),
                        ]:
                            fields[key] = ui.checkbox(label, value=data[key], on_change=lambda e, key=key: change(key, e.value))
                    elif number == 2:
                        ui.label(f"Write {cycle['min_words']}–{cycle['max_words']} words for each required response.").classes("text-gray-600")
                        for key, prompt in cycle["prompts"].items():
                            input_field(key, prompt + " *", textarea=True).props('autogrow maxlength="8000"')
                            counters[key] = ui.label(f"{len(data[key].split())}/{cycle['max_words']} words · {cycle['min_words']} minimum").classes("text-xs text-gray-600 self-end").props('aria-live="polite"')
                        input_field("experience", "Relevant experience (optional)", textarea=True).props('maxlength="2000"')
                    else:
                        review()
                        fields["certify"] = ui.checkbox("I have reviewed my answers and confirm this sample application is ready to submit. *", value=data["certify"], on_change=lambda e: change("certify", e.value))
                        ui.label("Your submitted application will be read-only.").classes("text-sm text-gray-600")
                    with ui.stepper_navigation():
                        actions.append(ui.button("Submit Application" if number == 3 else "Next", icon="check" if number == 3 else "arrow_forward", on_click=lambda number=number: act("submit" if number == 3 else "next", number)))
                        if number > 1:
                            actions.append(ui.button("Back", on_click=lambda number=number: go_to(number - 1)).props("flat"))
                        actions.append(ui.button("Save & exit", icon="save", on_click=lambda number=number: act("exit", number)).props("outline"))
