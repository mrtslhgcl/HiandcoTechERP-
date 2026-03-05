from PyQt5.QtWidgets import (QLineEdit, QComboBox, QMessageBox, QLabel,
                              QPushButton, QTextEdit, QCheckBox, QMenu,
                              QAction, QHBoxLayout, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from views.base_list_view import BaseListView
from views.base_dialog import BaseDialog
from controllers.customer_controller import CustomerController
from utils.theme import Theme


class CustomersView(BaseListView):
    def __init__(self):
        self.controller = CustomerController()

        columns = [
            {"key": "ID", "title": "ID", "width": 60, "align": "center"},
            {"key": "first_name", "title": "Ad"},
            {"key": "last_name", "title": "Soyad"},
            {"key": "phone_number", "title": "Telefon", "width": 140, "align": "center"},
            {"key": "email", "title": "E-posta", "width": 200},
            {"key": "address", "title": "Adres", "width": 200},
            {
                "key": "is_active", "title": "Durum", "width": 90, "align": "center",
                "render": lambda val, item: "Aktif" if val == 1 else "Pasif"
            },
            {"key": "created_at", "title": "Kayıt Tarihi", "width": 140, "align": "center",
             "render": lambda val, item: val[:16] if val else "-"},
        ]

        super().__init__(
            title="Müşteri Yönetimi",
            columns=columns,
            add_permission="customer_create",
            edit_permission="customer_update",
            delete_permission="customer_delete"
        )

        self.add_btn.setText("+ Yeni Müşteri")
        self._setup_context_menu()
        self.refresh_data()


    def _setup_context_menu(self):
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return

        start = (self.current_page - 1) * self.page_size
        data_index = start + row
        if data_index >= len(self.filtered_data):
            return

        item = self.filtered_data[data_index]

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Theme.BG_CARD};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 20px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {Theme.BG_HOVER};
            }}
        """)

        is_active = item.get("is_active", 1)
        toggle_text = "🔴 Pasife Al" if is_active == 1 else "🟢 Aktife Al"

        toggle_action = QAction(toggle_text, self)
        toggle_action.triggered.connect(lambda: self._toggle_active(item))
        menu.addAction(toggle_action)

        menu.addSeparator()

        edit_action = QAction("✏️ Düzenle", self)
        edit_action.triggered.connect(lambda: self._on_edit(item))
        menu.addAction(edit_action)

        delete_action = QAction("🗑️ Sil", self)
        delete_action.triggered.connect(lambda: self._on_delete(item))
        menu.addAction(delete_action)

        menu.exec_(self.table.viewport().mapToGlobal(pos))


    def _toggle_active(self, item: dict):
        is_active = item.get("is_active", 1)
        name = f"{item.get('first_name', '')} {item.get('last_name', '')}"

        if is_active == 1:
            result = self.controller.deactivate_customer(item["ID"])
        else:
            result = self.controller.activate_customer(item["ID"])

        if result["success"]:
            self.refresh_data()
        else:
            QMessageBox.warning(self, "Hata", result["message"])


    def _on_search(self, text: str):
        if not text.strip():
            self.filtered_data = self.data
        else:
            text_lower = text.lower()
            self.filtered_data = []
            for item in self.data:
                full_name = f"{item.get('first_name', '')} {item.get('last_name', '')}".lower()
                searchable = [
                    full_name,
                    str(item.get("phone_number", "")).lower(),
                    str(item.get("email", "")).lower(),
                    str(item.get("address", "")).lower(),
                    str(item.get("notes", "")).lower(),
                ]
                if any(text_lower in field for field in searchable):
                    self.filtered_data.append(item)

        self.current_page = 1
        self._update_pagination()
        self._render_table()


    def refresh_data(self):
        result = self.controller.get_all_customers()
        if result["success"]:
            self.set_data(result["data"])

    def _on_add(self):
        dialog = CustomerDialog(self)
        if dialog.exec_() == CustomerDialog.Accepted:
            data = dialog.result_data
            result = self.controller.add_customer(**data)
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _on_edit(self, item: dict):
        dialog = CustomerDialog(self, edit_data=item)
        if dialog.exec_() == CustomerDialog.Accepted:
            data = dialog.result_data
            result = self.controller.update_customer(item["ID"], data)
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _on_delete(self, item: dict):
        name = f"{item.get('first_name', '')} {item.get('last_name', '')}"
        if self.confirm_delete(name):
            result = self.controller.delete_customer(item["ID"])
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])


    def _render_table(self):
        super()._render_table()

        status_col = None
        for i, col in enumerate(self.columns):
            if col["key"] == "is_active":
                status_col = i
                break

        if status_col is not None:
            for row in range(self.table.rowCount()):
                cell = self.table.item(row, status_col)
                if cell:
                    if cell.text() == "Aktif":
                        cell.setForeground(QColor(Theme.SUCCESS))
                    else:
                        cell.setForeground(QColor(Theme.ERROR))


class CustomerDialog(BaseDialog):
    def __init__(self, parent=None, edit_data: dict = None):
        self.edit_data = edit_data

        title = "Müşteri Düzenle" if edit_data else "Yeni Müşteri Ekle"
        super().__init__(parent, title=title, width=500, height=550)

    def _setup_form(self):
        self.add_form_section_title("Kişisel Bilgiler")

        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("Müşteri adını girin")
        self.first_name_input.setStyleSheet(self._input_style())
        self.add_form_field("Ad", self.first_name_input, required=True)

        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Müşteri soyadını girin")
        self.last_name_input.setStyleSheet(self._input_style())
        self.add_form_field("Soyad", self.last_name_input, required=True)

        self.add_form_separator()
        self.add_form_section_title("İletişim Bilgileri")

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("0555 123 4567")
        self.phone_input.setStyleSheet(self._input_style())
        self.add_form_field("Telefon", self.phone_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("ornek@mail.com")
        self.email_input.setStyleSheet(self._input_style())
        self.add_form_field("E-posta", self.email_input)

        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("Adres bilgisi girin (opsiyonel)")
        self.address_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QTextEdit:focus {{
                border: 1px solid {Theme.BORDER_FOCUS};
            }}
        """)
        self.add_form_field("Adres", self.address_input, fixed_height=70)

        self.add_form_separator()
        self.add_form_section_title("Notlar")

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Müşteri hakkında notlar (opsiyonel)")
        self.notes_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QTextEdit:focus {{
                border: 1px solid {Theme.BORDER_FOCUS};
            }}
        """)
        self.add_form_field("Notlar", self.notes_input, fixed_height=70)

        if self.edit_data:
            self.first_name_input.setText(self.edit_data.get("first_name", ""))
            self.last_name_input.setText(self.edit_data.get("last_name", ""))
            self.phone_input.setText(self.edit_data.get("phone_number", ""))
            self.email_input.setText(self.edit_data.get("email", ""))
            self.address_input.setPlainText(self.edit_data.get("address", ""))
            self.notes_input.setPlainText(self.edit_data.get("notes", ""))

        self.form_layout.addStretch()

    def _on_save(self):
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()

        if not first_name:
            self.show_error("Müşteri adı boş bırakılamaz!")
            return

        if not last_name:
            self.show_error("Müşteri soyadı boş bırakılamaz!")
            return

        self.result_data = {
            "first_name": first_name,
            "last_name": last_name,
            "phone_number": self.phone_input.text().strip(),
            "email": self.email_input.text().strip(),
            "address": self.address_input.toPlainText().strip(),
            "notes": self.notes_input.toPlainText().strip(),
        }
        self.accept()

    def _input_style(self) -> str:
        return f"""
            QLineEdit, QComboBox {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 13px;
            }}
            QLineEdit:focus, QComboBox:focus {{
                border: 1px solid {Theme.BORDER_FOCUS};
            }}
        """
