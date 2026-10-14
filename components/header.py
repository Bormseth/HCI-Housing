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


def render_site_header():
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
            .home-content { max-width: 920px; margin: 58px auto 0; }
            .welcome-card { padding: 40px; border-radius: 24px; }
            .welcome-title { margin-top: 14px; color: #17324d;
                             font-size: clamp(32px, 5vw, 48px); font-weight: 800; }
            .welcome-copy { max-width: 650px; color: #536579; font-size: 17px;
                            line-height: 1.7; }
            .welcome-list { color: #536579; font-size: 16px; line-height: 1.7; }
            @media (max-width: 760px) {
                .site-nav { overflow-x: auto; flex-wrap: nowrap; }
            }
        </style>
    """)

    with ui.column().classes("site-shell w-full"):
        with ui.row().classes("brand-row w-full items-center"):
            if _LOGO_PATH.exists():
                ui.image("/unh-crest.png").classes("brand-logo")
            else:
                ui.label("UNH Housing Portal").classes("text-2xl font-bold")

        with ui.row().classes(
            "site-nav w-full items-center justify-between no-wrap"
        ):
            with ui.row().classes("items-center no-wrap"):
                for label, target in NAV_LEFT_LINKS:
                    ui.link(label, target)

            with ui.row().classes("items-center no-wrap"):
                for label, target in NAV_RIGHT_LINKS:
                    ui.link(label, target)
