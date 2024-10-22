# components/navigation.py

import dash_bootstrap_components as dbc
from dash import html

navbar = dbc.Navbar(
    [
        # Navigation links aligned to the left
        dbc.Nav(
            [
                dbc.NavItem(
                    dbc.NavLink(
                        [
                            html.I(className="fas fa-home"),  # Home icon
                            html.Span(" Home", className="nav-link-text")
                        ],
                        href="/",
                        active="exact",
                        className="nav-link-icon"
                    )
                ),
                dbc.NavItem(
                    dbc.NavLink(
                        [
                            html.I(className="fas fa-building"),  # Building icon
                            html.Span(" GNIRE Building 540", className="nav-link-text")
                        ],
                        href="/GNIREBUILDING540",
                        active="exact",
                        className="nav-link-icon"
                    )
                ),
                dbc.NavItem(
                    dbc.NavLink(
                        [
                            html.I(className="fas fa-building"),  # Building icon
                            html.Span(" GLEAMM Microgrid", className="nav-link-text")
                        ],
                        href="/building2",
                        active="exact",
                        className="nav-link-icon"
                    )
                ),
            ],
            navbar=True,
            className="nav-links",
        ),
        # Centered brand title
        dbc.NavbarBrand(
            "GROUP NIRE PRIORITY LOAD CONTROL PROGRAM",
            href="/",
            className="navbar-brand-center",
        ),
    ],
    color="dark",
    dark=True,
    sticky="top",
)
