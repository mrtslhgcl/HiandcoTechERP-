class Theme:
    BG_DARK = "#1a1a2e"
    BG_SIDEBAR = "#16213e"
    BG_CARD = "#0f3460"
    BG_INPUT = "#1a1a3e"
    BG_HOVER = "#1f4068"
    BG_TABLE_ROW = "#162447"
    BG_TABLE_ALT = "#1b2a4a"

    ACCENT = "#e94560"
    ACCENT_HOVER = "#ff6b81"
    ACCENT_LIGHT = "rgba(233, 69, 96, 0.15)"

    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#a6a6a6"
    TEXT_MUTED = "#6c7293"
    TEXT_DARK = "#1a1a2e"

    SUCCESS = "#4ecca3"
    ERROR = "#ff6b6b"
    WARNING = "#ffd93d"
    INFO = "#45b7d1"

    BORDER = "#2a2a4a"
    BORDER_LIGHT = "#3a3a5a"
    BORDER_FOCUS = "#e94560"

    FONT_FAMILY = "Segoe UI"
    FONT_SIZE_SMALL = 11
    FONT_SIZE_NORMAL = 13
    FONT_SIZE_LARGE = 16
    FONT_SIZE_TITLE = 22
    FONT_SIZE_HEADER = 28

    SIDEBAR_WIDTH = 240
    SIDEBAR_COLLAPSED_WIDTH = 60
    BORDER_RADIUS = 8
    BORDER_RADIUS_SMALL = 4
    BORDER_RADIUS_LARGE = 12
    INPUT_HEIGHT = 40
    BUTTON_HEIGHT = 40
    CARD_PADDING = 20

    @classmethod
    def get_stylesheet(cls) -> str:
        return f"""
            /* ===== GENEL ===== */
            QMainWindow, QWidget {{
                background-color: {cls.BG_DARK};
                color: {cls.TEXT_PRIMARY};
                font-family: {cls.FONT_FAMILY};
                font-size: {cls.FONT_SIZE_NORMAL}px;
            }}

            /* ===== LABEL ===== */
            QLabel {{
                color: {cls.TEXT_PRIMARY};
                font-family: {cls.FONT_FAMILY};
            }}

            /* ===== INPUT ===== */
            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
                background-color: {cls.BG_INPUT};
                color: {cls.TEXT_PRIMARY};
                border: 1px solid {cls.BORDER};
                border-radius: {cls.BORDER_RADIUS_SMALL}px;
                padding: 8px 12px;
                font-size: {cls.FONT_SIZE_NORMAL}px;
                min-height: {cls.INPUT_HEIGHT - 20}px;
            }}

            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 1px solid {cls.BORDER_FOCUS};
            }}

            QLineEdit:disabled, QTextEdit:disabled {{
                background-color: {cls.BG_SIDEBAR};
                color: {cls.TEXT_MUTED};
            }}

            /* ===== COMBOBOX ===== */
            QComboBox {{
                background-color: {cls.BG_INPUT};
                color: {cls.TEXT_PRIMARY};
                border: 1px solid {cls.BORDER};
                border-radius: {cls.BORDER_RADIUS_SMALL}px;
                padding: 8px 12px;
                min-height: {cls.INPUT_HEIGHT - 20}px;
            }}

            QComboBox:focus {{
                border: 1px solid {cls.BORDER_FOCUS};
            }}

            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}

            QComboBox QAbstractItemView {{
                background-color: {cls.BG_CARD};
                color: {cls.TEXT_PRIMARY};
                border: 1px solid {cls.BORDER};
                selection-background-color: {cls.ACCENT};
            }}

            /* ===== BUTON ===== */
            QPushButton {{
                background-color: {cls.ACCENT};
                color: {cls.TEXT_PRIMARY};
                border: none;
                border-radius: {cls.BORDER_RADIUS_SMALL}px;
                padding: 8px 20px;
                font-size: {cls.FONT_SIZE_NORMAL}px;
                font-weight: bold;
                min-height: {cls.BUTTON_HEIGHT - 20}px;
            }}

            QPushButton:hover {{
                background-color: {cls.ACCENT_HOVER};
            }}

            QPushButton:pressed {{
                background-color: {cls.ACCENT};
            }}

            QPushButton:disabled {{
                background-color: {cls.BG_HOVER};
                color: {cls.TEXT_MUTED};
            }}

            /* ===== TABLO ===== */
            QTableWidget {{
                background-color: {cls.BG_DARK};
                color: {cls.TEXT_PRIMARY};
                border: 1px solid {cls.BORDER};
                border-radius: {cls.BORDER_RADIUS_SMALL}px;
                gridline-color: {cls.BORDER};
                selection-background-color: {cls.ACCENT_LIGHT};
                selection-color: {cls.TEXT_PRIMARY};
            }}

            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {cls.BORDER};
            }}

            QTableWidget::item:selected {{
                background-color: {cls.ACCENT_LIGHT};
            }}

            QHeaderView::section {{
                background-color: {cls.BG_SIDEBAR};
                color: {cls.TEXT_PRIMARY};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {cls.ACCENT};
                font-weight: bold;
                font-size: {cls.FONT_SIZE_NORMAL}px;
            }}

            /* ===== SCROLLBAR ===== */
            QScrollBar:vertical {{
                background-color: {cls.BG_DARK};
                width: 8px;
                border-radius: 4px;
            }}

            QScrollBar::handle:vertical {{
                background-color: {cls.BORDER_LIGHT};
                border-radius: 4px;
                min-height: 30px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {cls.ACCENT};
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            QScrollBar:horizontal {{
                background-color: {cls.BG_DARK};
                height: 8px;
                border-radius: 4px;
            }}

            QScrollBar::handle:horizontal {{
                background-color: {cls.BORDER_LIGHT};
                border-radius: 4px;
                min-width: 30px;
            }}

            QScrollBar::handle:horizontal:hover {{
                background-color: {cls.ACCENT};
            }}

            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}

            /* ===== CHECKBOX ===== */
            QCheckBox {{
                color: {cls.TEXT_PRIMARY};
                spacing: 8px;
            }}

            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {cls.BORDER};
                border-radius: 3px;
                background-color: {cls.BG_INPUT};
            }}

            QCheckBox::indicator:checked {{
                background-color: {cls.ACCENT};
                border-color: {cls.ACCENT};
            }}

            /* ===== TAB ===== */
            QTabWidget::pane {{
                border: 1px solid {cls.BORDER};
                border-radius: {cls.BORDER_RADIUS_SMALL}px;
                background-color: {cls.BG_DARK};
            }}

            QTabBar::tab {{
                background-color: {cls.BG_SIDEBAR};
                color: {cls.TEXT_SECONDARY};
                padding: 10px 20px;
                border: none;
                border-bottom: 2px solid transparent;
            }}

            QTabBar::tab:selected {{
                color: {cls.TEXT_PRIMARY};
                border-bottom: 2px solid {cls.ACCENT};
            }}

            QTabBar::tab:hover {{
                color: {cls.TEXT_PRIMARY};
                background-color: {cls.BG_HOVER};
            }}

            /* ===== TOOLTIP ===== */
            QToolTip {{
                background-color: {cls.BG_CARD};
                color: {cls.TEXT_PRIMARY};
                border: 1px solid {cls.BORDER};
                border-radius: {cls.BORDER_RADIUS_SMALL}px;
                padding: 6px;
                font-size: {cls.FONT_SIZE_SMALL}px;
            }}

            /* ===== MESSAGE BOX ===== */
            QMessageBox {{
                background-color: {cls.BG_DARK};
                color: {cls.TEXT_PRIMARY};
            }}

            QMessageBox QLabel {{
                color: {cls.TEXT_PRIMARY};
            }}

            QMessageBox QPushButton {{
                min-width: 80px;
            }}

            /* ===== GROUP BOX ===== */
            QGroupBox {{
                border: 1px solid {cls.BORDER};
                border-radius: {cls.BORDER_RADIUS}px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
                color: {cls.TEXT_PRIMARY};
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }}
        """

    @classmethod
    def get_sidebar_button_style(cls, active: bool = False) -> str:
        bg = cls.ACCENT if active else "transparent"
        hover_bg = cls.ACCENT_HOVER if active else cls.BG_HOVER
        return f"""
            QPushButton {{
                background-color: {bg};
                color: {cls.TEXT_PRIMARY};
                border: none;
                border-radius: {cls.BORDER_RADIUS_SMALL}px;
                padding: 12px 20px;
                text-align: left;
                font-size: {cls.FONT_SIZE_NORMAL}px;
                font-weight: {'bold' if active else 'normal'};
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
            }}
        """

    @classmethod
    def get_card_style(cls) -> str:
        return f"""
            background-color: {cls.BG_CARD};
            border-radius: {cls.BORDER_RADIUS}px;
            padding: {cls.CARD_PADDING}px;
        """

    @classmethod
    def get_stat_card_style(cls, color: str = None) -> str:
        border_color = color or cls.ACCENT
        return f"""
            background-color: {cls.BG_CARD};
            border-left: 4px solid {border_color};
            border-radius: {cls.BORDER_RADIUS}px;
            padding: {cls.CARD_PADDING}px;
        """

    @classmethod
    def get_button_style(cls, variant: str = "primary") -> str:
        styles = {
            "primary": f"""
                QPushButton {{
                    background-color: {cls.ACCENT};
                    color: {cls.TEXT_PRIMARY};
                    border: none;
                    border-radius: {cls.BORDER_RADIUS_SMALL}px;
                    padding: 8px 20px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {cls.ACCENT_HOVER};
                }}
            """,
            "secondary": f"""
                QPushButton {{
                    background-color: {cls.BG_CARD};
                    color: {cls.TEXT_PRIMARY};
                    border: 1px solid {cls.BORDER};
                    border-radius: {cls.BORDER_RADIUS_SMALL}px;
                    padding: 8px 20px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {cls.BG_HOVER};
                }}
            """,
            "success": f"""
                QPushButton {{
                    background-color: {cls.SUCCESS};
                    color: {cls.TEXT_DARK};
                    border: none;
                    border-radius: {cls.BORDER_RADIUS_SMALL}px;
                    padding: 8px 20px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #5fddb5;
                }}
            """,
            "danger": f"""
                QPushButton {{
                    background-color: {cls.ERROR};
                    color: {cls.TEXT_PRIMARY};
                    border: none;
                    border-radius: {cls.BORDER_RADIUS_SMALL}px;
                    padding: 8px 20px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #ff8a8a;
                }}
            """,
            "outline": f"""
                QPushButton {{
                    background-color: transparent;
                    color: {cls.ACCENT};
                    border: 1px solid {cls.ACCENT};
                    border-radius: {cls.BORDER_RADIUS_SMALL}px;
                    padding: 8px 20px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {cls.ACCENT_LIGHT};
                }}
            """
        }
        return styles.get(variant, styles["primary"])

    @classmethod
    def get_outline_button_style(cls) -> str:
        return cls.get_button_style("outline")

    @classmethod
    def get_success_button_style(cls) -> str:
        return cls.get_button_style("success")

    @classmethod
    def get_danger_button_style(cls) -> str:
        return cls.get_button_style("danger")