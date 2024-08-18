from PySide6.QtGui import QColor, QGuiApplication, QPalette

from itaxotools.common.widgets import VectorIcon

# QApplication Style

style = "Fusion"


# Color definitions

colors = {
    "white": "#ffffff",
    "light": "#eff1ee",
    "beige": "#e1e0de",
    "gray": "#abaaa8",
    "iron": "#8b8d8a",
    "black": "#454241",
    "red": "#ee4e5f",
    "pink": "#eb9597",
    "orange": "#eb6a4a",
    "brown": "#655c5d",
    "green": "#00ff00",
}


# Colormaps for vector graphics and pixmaps

colormap = {
    VectorIcon.Normal: {
        "#000": colors["brown"],
        "#f00": colors["red"],
    },
    VectorIcon.Disabled: {
        "#000": colors["gray"],
        "#f00": colors["orange"],
    },
}

colormap_icon = {
    "#000": colors["black"],
    "#f00": colors["red"],
    "#f88": colors["pink"],
    "#ccc": colors["iron"],
}

colormap_icon_light = {
    "#000": colors["iron"],
    "#ff0000": colors["red"],
    "#ffa500": colors["pink"],
}


# Palette color scheme (using green for debugging)

scheme = {}
scheme[QPalette.Active] = {
    QPalette.Window: "light",
    QPalette.WindowText: "black",
    QPalette.Base: "white",
    QPalette.AlternateBase: "light",
    QPalette.PlaceholderText: "gray",
    QPalette.Text: "black",
    QPalette.Button: "light",
    QPalette.ButtonText: "black",
    QPalette.Light: "white",
    QPalette.Midlight: "beige",
    QPalette.Mid: "gray",
    QPalette.Dark: "iron",
    QPalette.Shadow: "brown",
    QPalette.Highlight: "red",
    QPalette.HighlightedText: "white",
    # These work on linux only?
    QPalette.ToolTipBase: "beige",
    QPalette.ToolTipText: "brown",
    # These seem bugged anyway
    QPalette.BrightText: "green",
    QPalette.Link: "red",
    QPalette.LinkVisited: "pink",
}
scheme[QPalette.Disabled] = {
    QPalette.Window: "light",
    QPalette.WindowText: "iron",
    QPalette.Base: "white",
    QPalette.AlternateBase: "light",
    QPalette.PlaceholderText: "gray",
    QPalette.Text: "iron",
    QPalette.Button: "light",
    QPalette.ButtonText: "gray",
    QPalette.Light: "white",
    QPalette.Midlight: "beige",
    QPalette.Mid: "gray",
    QPalette.Dark: "iron",
    QPalette.Shadow: "brown",
    QPalette.Highlight: "pink",
    QPalette.HighlightedText: "white",
    # These seem bugged anyway
    QPalette.BrightText: "green",
    QPalette.ToolTipBase: "green",
    QPalette.ToolTipText: "green",
    QPalette.Link: "green",
    QPalette.LinkVisited: "green",
}
scheme[QPalette.Inactive] = scheme[QPalette.Active]


def apply(app: QGuiApplication):
    app.setStyle(style)
    palette = app.palette()
    for group in scheme:
        for role in scheme[group]:
            palette.setColor(group, role, QColor(colors[scheme[group][role]]))
    app.setPalette(palette)
