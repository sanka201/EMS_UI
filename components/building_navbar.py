# components/building_navbar.py

import dash_bootstrap_components as dbc
from dash import html

def create_building_navbar(building_id):
    """
    Creates a secondary navigation bar for the given building.
    building_id: A unique identifier for the building (e.g., 'building1').
    """

    # Define the navigation items with labels, icons, and hrefs
    nav_links = [
        {'label': 'Devices Info', 'icon_class': 'fas fa-info-circle', 'href': f'/{building_id}/devices'},
        {'label': 'Schedule', 'icon_class': 'fas fa-calendar-alt', 'href': f'/{building_id}/schedule'},
        {'label': 'Control', 'icon_class': 'fas fa-sliders-h', 'href': f'/{building_id}/control'},
        {'label': 'Analytics', 'icon_class': 'fas fa-chart-line ', 'href': f'/{building_id}/analytics'}
    ]

    nav_items = []
    for link in nav_links:
        nav_items.append(
            dbc.NavItem(
                dbc.NavLink(
                    [
                        html.I(className=link['icon_class']),
                        html.Span(link['label'], className='ml-2')
                    ],
                    href=link['href'],
                    active='exact',
                    external_link=False,
                    className='building-nav-link'
                )
            )
        )

    building_navbar = dbc.Navbar(
        dbc.Container(
            [
                dbc.Nav(
                    nav_items,
                    navbar=True,
                    className='mr-auto',  # Aligns nav items to the left
                ),
                        # Centered brand title
        dbc.NavbarBrand(
            f"{building_id}",
            href="/",
            className="navbar-brand-center",
        ),
            ],
            fluid=True,  # Make the container fluid to span full width
            
        ),
        color='light',
        dark=False,
        className='secondary-nav',
        
        
    )

    return building_navbar
