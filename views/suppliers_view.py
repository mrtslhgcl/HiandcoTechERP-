from PyQt5.QtWidgets import (QLineEdit, QComboBox, QMessageBox, QLabel,
                              QPushButton, QFileDialog, QHBoxLayout, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from views.base_list_view import BaseListView
from views.base_dialog import BaseDialog
from controllers.supplier_controller import SupplierController
from utils.theme import Theme
from utils.image_utils import save_entity_image, resolve_image_path
import os


class SuppliersView(BaseListView):
    def __init__(self):
        self.controller = SupplierController()

        columns = [
            {"key": "ID", "title": "ID", "width": 60, "align": "center"},
            {"key": "name", "title": "Tedarikçi Adı"},
            {"key": "authorized_person", "title": "Yetkili Kişi", "width": 150},
            {"key": "phone", "title": "Telefon", "width": 130, "align": "center"},
            {"key": "email", "title": "E-posta", "width": 180},
            {
                "key": "is_active", "title": "Durum", "width": 90, "align": "center",
                "render": lambda val, item: "Aktif" if val == 1 else "Pasif"
            },
            {"key": "created_at", "title": "Oluşturulma", "width": 140, "align": "center",
             "render": lambda val, item: val[:16] if val else "-"},
        ]

        super().__init__(
            title="Tedarikçi Yönetimi",
            columns=columns,
            add_permission="supplier_create",
            edit_permission="supplier_update",
            delete_permission="supplier_delete"
        )

        self.add_btn.setText("+ Yeni Tedarikçi")
        self.refresh_data()

    def refresh_data(self):
        data = self.controller.supplier_repo.get_all()
        self.set_data(data)

    def _on_add(self):
        dialog = SupplierDialog(self)
        if dialog.exec_() == SupplierDialog.Accepted:
            data = dialog.result_data
            logo_source = data.pop("logo", "")
            data.pop("_logo_changed", None)

            result = self.controller.add_supplier(**data)
            if result["success"]:
                supplier_id = result.get("supplier_id")
                if logo_source and supplier_id:
                    rel_path, b64_data = save_entity_image(logo_source, "suppliers", supplier_id)
                    update = {"logo": rel_path}
                    if b64_data:
                        update["image_data"] = b64_data
                    self.controller.supplier_repo.update(supplier_id, update)
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _on_edit(self, item: dict):
        dialog = SupplierDialog(self, edit_data=item)
        if dialog.exec_() == SupplierDialog.Accepted:
            data = dialog.result_data
            logo_source = data.pop("logo", "")
            logo_changed = data.pop("_logo_changed", False)

            if logo_changed:
                if logo_source:
                    rel_path, b64_data = save_entity_image(logo_source, "suppliers", item["ID"])
                    data["logo"] = rel_path
                    if b64_data:
                        data["image_data"] = b64_data
                else:
                    data["logo"] = ""
                    data["image_data"] = ""

            result = self.controller.update_supplier(item["ID"], data)
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _on_delete(self, item: dict):
        name = item.get("name", "")
        if self.confirm_delete(name):
            result = self.controller.delete_supplier(item["ID"])
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])


class SupplierDialog(BaseDialog):
    def __init__(self, parent=None, edit_data: dict = None):
        self.edit_data = edit_data
        self._logo_changed = False

        if edit_data:
            stored_path = edit_data.get("logo", "")
            image_data = edit_data.get("image_data", "")
            self.selected_logo_path = resolve_image_path(stored_path, image_data) or ""
        else:
            self.selected_logo_path = ""

        title = "Tedarikçi Düzenle" if edit_data else "Yeni Tedarikçi Ekle"
        super().__init__(parent, title=title, width=520, height=620)

    def _setup_form(self):
        self.add_form_section_title("Logo")

        logo_widget = QWidget()
        logo_widget.setStyleSheet("background: transparent;")
        logo_layout = QHBoxLayout(logo_widget)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(15)

        self.logo_preview = QLabel()
        self.logo_preview.setFixedSize(64, 64)
        self.logo_preview.setAlignment(Qt.AlignCenter)
        self.logo_preview.setStyleSheet(f"""
            QLabel {{
                background-color: {Theme.BG_INPUT};
                border: 2px dashed {Theme.BORDER};
                border-radius: 8px;
            }}
        """)
        self._update_logo_preview()
        logo_layout.addWidget(self.logo_preview)

        logo_btn_layout = QWidget()
        logo_btn_layout.setStyleSheet("background: transparent;")
        logo_btn_inner = QHBoxLayout(logo_btn_layout)
        logo_btn_inner.setContentsMargins(0, 0, 0, 0)
        logo_btn_inner.setSpacing(8)

        select_logo_btn = QPushButton("Logo Seç")
        select_logo_btn.setCursor(Qt.PointingHandCursor)
        select_logo_btn.setFixedHeight(34)
        select_logo_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.INFO};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 15px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #5bc7e0; }}
        """)
        select_logo_btn.clicked.connect(self._select_logo)
        logo_btn_inner.addWidget(select_logo_btn)

        clear_logo_btn = QPushButton("Kaldır")
        clear_logo_btn.setCursor(Qt.PointingHandCursor)
        clear_logo_btn.setFixedHeight(34)
        clear_logo_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ERROR};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 15px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #ff8a8a; }}
        """)
        clear_logo_btn.clicked.connect(self._clear_logo)
        logo_btn_inner.addWidget(clear_logo_btn)
        logo_btn_inner.addStretch()

        logo_layout.addWidget(logo_btn_layout)
        logo_layout.addStretch()
        self.form_layout.addWidget(logo_widget)

        self.add_form_separator()
        self.add_form_section_title("Firma Bilgileri")

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Firma / tedarikçi adını girin")
        self.name_input.setStyleSheet(self._input_style())
        self.add_form_field("Tedarikçi Adı", self.name_input, required=True)

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Açıklama (opsiyonel)")
        self.desc_input.setStyleSheet(self._input_style())
        self.add_form_field("Açıklama", self.desc_input)

        self.add_form_separator()
        self.add_form_section_title("İletişim Bilgileri")

        self.authorized_input = QLineEdit()
        self.authorized_input.setPlaceholderText("Yetkili kişi adı")
        self.authorized_input.setStyleSheet(self._input_style())
        self.add_form_field("Yetkili Kişi", self.authorized_input)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("0555 123 4567")
        self.phone_input.setStyleSheet(self._input_style())
        self.add_form_field("Telefon", self.phone_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("ornek@firma.com")
        self.email_input.setStyleSheet(self._input_style())
        self.add_form_field("E-posta", self.email_input)

        self.add_form_separator()
        self.add_form_section_title("Finans & Adres")

        self.iban_input = QLineEdit()
        self.iban_input.setPlaceholderText("TR00 0000 0000 0000 0000 0000 00")
        self.iban_input.setStyleSheet(self._input_style())
        self.add_form_field("IBAN", self.iban_input)

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Adres detayı")
        self.address_input.setStyleSheet(self._input_style())
        self.add_form_field("Adres", self.address_input)

        if self.edit_data:
            self.name_input.setText(self.edit_data.get("name", ""))
            self.desc_input.setText(self.edit_data.get("description", ""))
            self.authorized_input.setText(self.edit_data.get("authorized_person", ""))
            self.phone_input.setText(self.edit_data.get("phone", ""))
            self.email_input.setText(self.edit_data.get("email", ""))
            self.iban_input.setText(self.edit_data.get("IBAN", ""))
            self.address_input.setText(self.edit_data.get("address", ""))

        self.form_layout.addStretch()

    def _select_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Logo Seç", "",
            "Resim Dosyaları (*.png *.jpg *.jpeg *.bmp *.ico)"
        )
        if file_path:
            self.selected_logo_path = file_path
            self._logo_changed = True
            self._update_logo_preview()

    def _clear_logo(self):
        self.selected_logo_path = ""
        self._logo_changed = True
        self._update_logo_preview()

    def _update_logo_preview(self):
        if self.selected_logo_path and os.path.exists(self.selected_logo_path):
            pixmap = QPixmap(self.selected_logo_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.logo_preview.setPixmap(scaled)
                return

        self.logo_preview.clear()
        self.logo_preview.setText("🏢")
        self.logo_preview.setStyleSheet(f"""
            QLabel {{
                background-color: {Theme.BG_INPUT};
                border: 2px dashed {Theme.BORDER};
                border-radius: 8px;
                font-size: 28px;
            }}
        """)

    def _on_save(self):
        name = self.name_input.text().strip()
        if not name:
            self.show_error("Tedarikçi adı boş bırakılamaz!")
            return

        self.result_data = {
            "name": name,
            "description": self.desc_input.text().strip(),
            "authorized_person": self.authorized_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "email": self.email_input.text().strip(),
            "IBAN": self.iban_input.text().strip(),
            "address": self.address_input.text().strip(),
            "logo": self.selected_logo_path,
            "_logo_changed": self._logo_changed,
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