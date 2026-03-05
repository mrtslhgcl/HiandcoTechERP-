from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QWidget, QScrollArea, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from utils.theme import Theme


class BaseDialog(QDialog):
    def __init__(self, parent=None, title: str = "", width: int = 500, height: int = 500):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(width, height)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._drag_pos = None
        self.result_data = None

        self._setup_base_ui(title)

    def _setup_base_ui(self, title: str):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self.container = QFrame()
        self.container.setObjectName("dialogContainer")
        self.container.setStyleSheet(f"""
            QFrame#dialogContainer {{
                background-color: {Theme.BG_DARK};
                border-radius: 12px;
                border: 1px solid {Theme.BORDER};
            }}
        """)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SIDEBAR};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom: 1px solid {Theme.BORDER};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 10, 0)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; background: transparent;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_SECONDARY};
                border: none;
                font-size: 16px;
                border-radius: 16px;
            }}
            QPushButton:hover {{
                background-color: {Theme.ERROR};
                color: white;
            }}
        """)
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)

        container_layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {Theme.BG_DARK};
            }}
        """)

        self.form_widget = QWidget()
        self.form_layout = QVBoxLayout(self.form_widget)
        self.form_layout.setContentsMargins(25, 20, 25, 10)
        self.form_layout.setSpacing(15)

        scroll.setWidget(self.form_widget)
        container_layout.addWidget(scroll)

        footer = QFrame()
        footer.setFixedHeight(60)
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SIDEBAR};
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
                border-top: 1px solid {Theme.BORDER};
            }}
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 0, 20, 0)
        footer_layout.addStretch()

        self.cancel_btn = QPushButton("İptal")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setFixedSize(100, 36)
        self.cancel_btn.setStyleSheet(Theme.get_outline_button_style())
        self.cancel_btn.clicked.connect(self.reject)
        footer_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("💾 Kaydet")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setFixedSize(120, 36)
        self.save_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.SUCCESS};
                color: {Theme.TEXT_DARK};
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #5fddb5;
            }}
        """)
        self.save_btn.clicked.connect(self._on_save)
        footer_layout.addWidget(self.save_btn)

        container_layout.addWidget(footer)
        outer_layout.addWidget(self.container)

        self._setup_form()


    from PyQt5.QtCore import Qt

    def add_form_field(self, label: str, widget: QWidget, required: bool = False, fixed_height: int = 38):
        field_layout = QVBoxLayout()
        field_layout.setContentsMargins(0, 0, 0, 0)
        field_layout.setSpacing(5)

        label_text = f"{label} *" if required else label
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"""
            color: {Theme.TEXT_SECONDARY};
            font-size: 12px;
            font-weight: bold;
            background: transparent;
        """)
        field_layout.addWidget(lbl)

        if fixed_height is not None:
            widget.setFixedHeight(fixed_height)

        field_layout.addWidget(widget, 0, Qt.AlignTop)

        self.form_layout.addLayout(field_layout)
        return widget

    def add_form_separator(self):
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {Theme.BORDER};")
        self.form_layout.addWidget(sep)

    def add_form_section_title(self, title: str):
        lbl = QLabel(title)
        lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        lbl.setStyleSheet(f"color: {Theme.ACCENT}; background: transparent;")
        self.form_layout.addWidget(lbl)

    def show_error(self, message: str):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.warning(self, "Hata", message)

    def show_success(self, message: str):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Başarılı", message)


    def _on_save(self):
        pass

    def _setup_form(self):
        pass


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.pos().y() < 50:
            self._drag_pos = event.globalPos() - self.pos()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None