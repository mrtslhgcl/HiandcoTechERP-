from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QTableWidget,
                              QTableWidgetItem, QHeaderView, QComboBox,
                              QMessageBox, QFrame, QSpinBox, QAbstractItemView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from utils.theme import Theme
from utils.permission_helper import has_permission
import math


class BaseListView(QWidget):
    def __init__(self, title: str, columns: list[dict],
                 add_permission: str = "", edit_permission: str = "",
                 delete_permission: str = "",
                 page_size: int = 100):
        super().__init__()
        self.title = title
        self.columns = columns
        self.add_permission = add_permission
        self.edit_permission = edit_permission
        self.delete_permission = delete_permission
        self.data = []
        self.filtered_data = []

        self.page_size = page_size
        self.current_page = 1
        self.total_pages = 1

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(15)

        title_label = QLabel(self.title)
        title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        layout.addWidget(title_label)

        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        self.table = self._create_table()
        layout.addWidget(self.table)

        footer = self._create_footer()
        layout.addWidget(footer)

    def _create_toolbar(self) -> QWidget:
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border-radius: {Theme.BORDER_RADIUS}px;
                padding: 8px;
            }}
        """)

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 16px; background: transparent;")
        layout.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara...")
        self.search_input.setFixedHeight(36)
        self.search_input.setFixedWidth(250)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {Theme.BORDER_FOCUS};
            }}
        """)
        self.search_input.textChanged.connect(self._on_search)
        layout.addWidget(self.search_input)

        self.filter_layout = QHBoxLayout()
        self.filter_layout.setSpacing(8)
        layout.addLayout(self.filter_layout)

        layout.addStretch()

        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setFixedHeight(36)
        refresh_btn.setStyleSheet(Theme.get_outline_button_style())
        refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_btn)

        self.add_btn = QPushButton("+ Yeni Ekle")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setFixedHeight(36)
        self.add_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT_HOVER};
            }}
        """)
        self.add_btn.clicked.connect(self._on_add)

        if self.add_permission and not has_permission(self.add_permission):
            self.add_btn.setVisible(False)

        layout.addWidget(self.add_btn)

        return toolbar

    def _create_table(self) -> QTableWidget:
        col_count = len(self.columns) + 1

        table = QTableWidget()
        table.setColumnCount(col_count)

        headers = [c["title"] for c in self.columns] + ["İşlemler"]
        table.setHorizontalHeaderLabels(headers)

        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setSortingEnabled(False)
        table.setRowCount(0)

        self._sort_column = -1
        self._sort_order = Qt.AscendingOrder

        table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)

        header = table.horizontalHeader()
        has_stretch = False
        for i, col in enumerate(self.columns):
            if "width" in col:
                header.setSectionResizeMode(i, QHeaderView.Fixed)
                header.resizeSection(i, col["width"])
            else:
                header.setSectionResizeMode(i, QHeaderView.Stretch)
                has_stretch = True

        header.setSectionResizeMode(col_count - 1, QHeaderView.Fixed)
        header.resizeSection(col_count - 1, 220)

        if not has_stretch and len(self.columns) > 0:
            header.setSectionResizeMode(0, QHeaderView.Stretch)

        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Theme.BG_DARK};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                gridline-color: transparent;
                selection-background-color: {Theme.ACCENT};
                selection-color: white;
                alternate-background-color: rgba(255, 255, 255, 0.03);
            }}
            QTableWidget::item {{
                padding: 10px 8px;
                border-bottom: 1px solid {Theme.BORDER};
                color: {Theme.TEXT_PRIMARY};
            }}
            QTableWidget::item:alternate {{
                background-color: rgba(255, 255, 255, 0.03);
                color: {Theme.TEXT_PRIMARY};
            }}
            QTableWidget::item:selected {{
                background-color: {Theme.ACCENT};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {Theme.BG_SIDEBAR};
                color: {Theme.TEXT_PRIMARY};
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid {Theme.ACCENT};
                font-weight: bold;
                font-size: 12px;
            }}
        """)

        return table

    def _create_footer(self) -> QWidget:
        footer = QFrame()
        footer.setFixedHeight(46)
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border-radius: 6px;
            }}
        """)

        layout = QHBoxLayout(footer)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(10)

        self.total_label = QLabel("Toplam: 0 kayıt")
        self.total_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        layout.addWidget(self.total_label)

        layout.addStretch()

        pagination_style = f"""
            QPushButton {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: bold;
                min-width: 32px;
            }}
            QPushButton:hover {{ background-color: {Theme.BG_HOVER}; }}
            QPushButton:disabled {{ color: {Theme.TEXT_MUTED}; background-color: {Theme.BG_DARK}; }}
        """

        self.btn_first = QPushButton("«")
        self.btn_first.setToolTip("İlk Sayfa")
        self.btn_first.setCursor(Qt.PointingHandCursor)
        self.btn_first.setStyleSheet(pagination_style)
        self.btn_first.clicked.connect(lambda: self._go_to_page(1))
        layout.addWidget(self.btn_first)

        self.btn_prev = QPushButton("‹ Önceki")
        self.btn_prev.setCursor(Qt.PointingHandCursor)
        self.btn_prev.setStyleSheet(pagination_style)
        self.btn_prev.clicked.connect(lambda: self._go_to_page(self.current_page - 1))
        layout.addWidget(self.btn_prev)

        self.page_spin = QSpinBox()
        self.page_spin.setRange(1, 1)
        self.page_spin.setValue(1)
        self.page_spin.setFixedWidth(60)
        self.page_spin.setAlignment(Qt.AlignCenter)
        self.page_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 4px;
                font-size: 12px;
                font-weight: bold;
            }}
        """)
        self.page_spin.valueChanged.connect(self._on_page_spin_changed)
        layout.addWidget(self.page_spin)

        self.page_info_label = QLabel("/ 1")
        self.page_info_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        layout.addWidget(self.page_info_label)

        self.btn_next = QPushButton("Sonraki ›")
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.setStyleSheet(pagination_style)
        self.btn_next.clicked.connect(lambda: self._go_to_page(self.current_page + 1))
        layout.addWidget(self.btn_next)

        self.btn_last = QPushButton("»")
        self.btn_last.setToolTip("Son Sayfa")
        self.btn_last.setCursor(Qt.PointingHandCursor)
        self.btn_last.setStyleSheet(pagination_style)
        self.btn_last.clicked.connect(lambda: self._go_to_page(self.total_pages))
        layout.addWidget(self.btn_last)

        sep = QLabel("|")
        sep.setStyleSheet(f"color: {Theme.BORDER}; background: transparent;")
        layout.addWidget(sep)

        size_label = QLabel("Sayfa:")
        size_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        layout.addWidget(size_label)

        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["50", "100", "200", "500"])
        self.page_size_combo.setCurrentText(str(self.page_size))
        self.page_size_combo.setFixedWidth(70)
        self.page_size_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Theme.BG_SIDEBAR};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                selection-background-color: {Theme.BG_HOVER};
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox::down-arrow {{ image: none; }}
        """)
        self.page_size_combo.currentTextChanged.connect(self._on_page_size_changed)
        layout.addWidget(self.page_size_combo)

        return footer


    def set_data(self, data: list[dict]):
        self.data = data
        self.filtered_data = data
        self.current_page = 1
        self._update_pagination()
        self._render_table()

    def refresh_data(self):
        pass

    def _update_pagination(self):
        total = len(self.filtered_data)
        self.total_pages = max(1, math.ceil(total / self.page_size))

        if self.current_page > self.total_pages:
            self.current_page = self.total_pages

        self.page_spin.blockSignals(True)
        self.page_spin.setRange(1, self.total_pages)
        self.page_spin.setValue(self.current_page)
        self.page_spin.blockSignals(False)

        self.page_info_label.setText(f"/ {self.total_pages}")

        self.btn_first.setEnabled(self.current_page > 1)
        self.btn_prev.setEnabled(self.current_page > 1)
        self.btn_next.setEnabled(self.current_page < self.total_pages)
        self.btn_last.setEnabled(self.current_page < self.total_pages)

        start = (self.current_page - 1) * self.page_size + 1
        end = min(self.current_page * self.page_size, total)
        if total == 0:
            self.total_label.setText("Kayıt bulunamadı")
        else:
            self.total_label.setText(f"Toplam {total} kayıttan {start}-{end} arası gösteriliyor")

    def _go_to_page(self, page: int):
        page = max(1, min(page, self.total_pages))
        if page != self.current_page:
            self.current_page = page
            self._update_pagination()
            self._render_table()

    def _on_page_spin_changed(self, value: int):
        self._go_to_page(value)

    def _on_page_size_changed(self, text: str):
        try:
            self.page_size = int(text)
        except ValueError:
            return
        self.current_page = 1
        self._update_pagination()
        self._render_table()

    def _render_table(self):
        self.table.setRowCount(0)

        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        page_data = self.filtered_data[start:end]

        self.table.setRowCount(len(page_data))

        for row, item in enumerate(page_data):
            self.table.setRowHeight(row, 45)

            for col, column_def in enumerate(self.columns):
                key = column_def["key"]
                value = item.get(key, "")

                renderer = column_def.get("render")
                if renderer:
                    display_text = renderer(value, item)
                else:
                    display_text = str(value) if value is not None else ""

                cell = QTableWidgetItem(display_text)
                cell.setData(Qt.UserRole, item.get("ID"))

                align = column_def.get("align", "left")
                if align == "center":
                    cell.setTextAlignment(Qt.AlignCenter)
                elif align == "right":
                    cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                self.table.setItem(row, col, cell)

            self._create_action_buttons(row, item)

        header = self.table.horizontalHeader()
        if self._sort_column >= 0:
            header.setSortIndicator(self._sort_column, self._sort_order)
            header.setSortIndicatorShown(True)
        else:
            header.setSortIndicatorShown(False)

    def _create_action_buttons(self, row: int, item: dict):
        actions_widget = QWidget()
        actions_widget.setStyleSheet("background: transparent;")
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(8, 4, 8, 4)
        actions_layout.setSpacing(8)

        if not self.edit_permission or has_permission(self.edit_permission):
            edit_btn = QPushButton("Düzenle")
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.setFixedSize(80, 28)
            edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.INFO};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0 8px;
                }}
                QPushButton:hover {{
                    background-color: #5bc7e0;
                }}
            """)
            edit_btn.clicked.connect(lambda checked, i=item: self._on_edit(i))
            actions_layout.addWidget(edit_btn)

        if not self.delete_permission or has_permission(self.delete_permission):
            del_btn = QPushButton("Sil")
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setFixedSize(60, 28)
            del_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.ERROR};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0 8px;
                }}
                QPushButton:hover {{
                    background-color: #ff8a8a;
                }}
            """)
            del_btn.clicked.connect(lambda checked, i=item: self._on_delete(i))
            actions_layout.addWidget(del_btn)

        actions_layout.addStretch()
        self.table.setCellWidget(row, len(self.columns), actions_widget)


    def _on_header_clicked(self, logical_index: int):
        if logical_index >= len(self.columns):
            return

        column_def = self.columns[logical_index]

        if self._sort_column == logical_index:
            self._sort_order = Qt.DescendingOrder if self._sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            self._sort_column = logical_index
            self._sort_order = Qt.AscendingOrder

        renderer = column_def.get("render")
        key = column_def["key"]

        def sort_key(item):
            if renderer:
                val = renderer(item.get(key, ""), item)
            else:
                val = item.get(key, "")
            if val is None:
                return ""
            try:
                return float(val)
            except (ValueError, TypeError):
                return str(val).lower()

        reverse = (self._sort_order == Qt.DescendingOrder)
        self.filtered_data.sort(key=sort_key, reverse=reverse)

        self.current_page = 1
        self._update_pagination()
        self._render_table()

    def _on_search(self, text: str):
        if not text.strip():
            self.filtered_data = self.data
        else:
            text_lower = text.lower()
            self.filtered_data = []
            for item in self.data:
                for col in self.columns:
                    value = str(item.get(col["key"], "")).lower()
                    if text_lower in value:
                        self.filtered_data.append(item)
                        break

        self.current_page = 1
        self._update_pagination()
        self._render_table()

    def _on_add(self):
        pass

    def _on_edit(self, item: dict):
        pass

    def _on_delete(self, item: dict):
        pass

    def confirm_delete(self, item_name: str = "") -> bool:
        msg = f"'{item_name}' kaydını silmek istediğinize emin misiniz?" if item_name else "Bu kaydı silmek istediğinize emin misiniz?"
        reply = QMessageBox.question(
            self, "Silme Onayı", msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        return reply == QMessageBox.Yes