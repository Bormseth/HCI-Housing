from pathlib import Path

from nicegui import app, ui

_LOGO_PATH = Path(__file__).resolve().parents[1] / "Media" / "UNH-CREST.png"

# Register the logo once when this module is imported.
if _LOGO_PATH.exists():
    app.add_static_file(local_file=_LOGO_PATH, url_path="/unh-crest.png")

NAV_LEFT_LINKS = [
    ("Home", "/"),
    ("Housing Applications", "/housing-applications"),
    ("Meal Plans", "/meal-plans"),
    ("Become an RA", "/become-an-ra"),
]

NAV_RIGHT_LINKS = [
    ("My Profile", "/my-profile"),
    ("Messages", "/messages"),
    ("Log out", "/"),
]


def render_site_header(active_path: str = ""):
    """Render the shared portal header and navigation."""
    ui.add_head_html("""
        <style>
            body { background: #f4f7fb; color: #182536; }
            .site-shell { max-width: 1180px; margin: auto; padding: 22px 28px; }
            .brand-row { min-height: 170px; }
            .brand-logo { display: block; width: 480px; max-width: 100%; height: auto; }
            .site-nav { gap: 8px; margin: 18px 0 34px; padding: 10px 14px;
                        background: white; border-radius: 14px; }
            .site-nav a { padding: 10px 12px; color: #34495e; font-weight: 600;
                          white-space: nowrap; }
            .site-nav a[aria-current="page"] { background: #eaf0fa; color: #073b78;
                          border-radius: 7px; text-decoration: none; }
            .application-banner { width: 100%; padding: 12px 16px; border-radius: 8px;
                                  background: #eaf0fa; color: #17324d; gap: 10px; }
            .application-grid { width: 100%; display: grid;
                                grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px; }
            .application-content { width: 100%; max-width: 1180px; margin: auto;
                                   padding: 22px 28px; gap: 24px; }
            .application-form { max-width: 920px; }
            .application-errors { width: 100%; padding: 12px 16px; border-radius: 8px;
                                  background: #fff3f0; color: #922b1c; border: 1px solid #edc1b7; }
            .application-answer { white-space: pre-wrap; overflow-wrap: anywhere; }
            .application-content a:focus-visible, .application-content button:focus-visible,
            .site-nav a:focus-visible { outline: 3px solid #da8e00; outline-offset: 3px; }
            .home-content { max-width: 920px; margin: 58px auto 0; }
            .welcome-card { padding: 40px; border-radius: 24px; }
            .welcome-title { margin-top: 14px; color: #17324d;
                             font-size: clamp(32px, 5vw, 48px); font-weight: 800; }
            .welcome-copy { max-width: 650px; color: #536579; font-size: 17px;
                            line-height: 1.7; }
            .welcome-list { color: #536579; font-size: 16px; line-height: 1.7; }
            @media (max-width: 760px) {
                .application-grid { grid-template-columns: minmax(0, 1fr); }
                .application-content { padding: 16px; gap: 18px; }
                .application-stepper .q-stepper__header { flex-wrap: nowrap; }
                .application-stepper .q-stepper__tab { padding: 12px 6px; min-width: 0; flex: 1; }
                .application-stepper .q-stepper__label { min-width: 0; }
                .application-stepper .q-stepper__title { font-size: 12px; white-space: normal; }
                .application-stepper .q-stepper__step-inner { padding: 20px 16px; }
                .site-shell { padding: 16px; }
                .brand-row { min-height: 100px; }
                .site-nav { flex-wrap: wrap; padding: 6px; gap: 4px; }
                .site-nav > .row { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); width: 100%; gap: 0; }
                .site-nav > .row:last-child { grid-template-columns: repeat(3, minmax(0, 1fr)); }
                .site-nav a { padding: 8px 4px; min-height: 44px; white-space: normal;
                              text-align: center; display: flex; align-items: center;
                              justify-content: center; font-size: 12px; line-height: 1.35; }
            }
        </style>
    """)

    with ui.column().classes("site-shell w-full"):
        with ui.row().classes("brand-row w-full items-center"):
            if _LOGO_PATH.exists():
                ui.image("/unh-crest.png").classes("brand-logo").props('alt="University of New Hampshire"')
            else:
                ui.label("UNH Housing Portal").classes("text-2xl font-bold")

        with ui.row().classes(
            "site-nav w-full items-center justify-between no-wrap"
        ):
            with ui.row().classes("items-center no-wrap"):
                for label, target in NAV_LEFT_LINKS:
                    link = ui.link(label, target)
                    if target == active_path:
                        link.props('aria-current="page"')

            with ui.row().classes("items-center no-wrap"):
                for label, target in NAV_RIGHT_LINKS:
                    link = ui.link(label, target)
                    if target == active_path:
                        link.props('aria-current="page"')
