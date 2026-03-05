from PyQt5.QtWidgets import (QLineEdit, QComboBox, QMessageBox, QLabel,
                              QPushButton, QFileDialog, QHBoxLayout, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from views.base_list_view import BaseListView
from views.base_dialog import BaseDialog
from controllers.brand_controller import BrandController
from utils.theme import Theme
from utils.image_utils import save_entity_image, resolve_image_path
import os


class BrandsView(BaseListView):
    def __init__(self):
        self.controller = BrandController()

        columns = [
            {"key": "ID", "title": "ID", "width": 60, "align": "center"},
            {"key": "logo_path", "title": "Logo", "width": 60, "align": "center"},
            {"key": "name", "title": "Marka Adı"},
            {"key": "description", "title": "Açıklama"},
            {"key": "created_at", "title": "Oluşturulma", "width": 150, "align": "center",
             "render": lambda val, item: val[:16] if val else "-"},
        ]

        super().__init__(
            title="Marka Yönetimi",
            columns=columns,
            add_permission="brand_create",
            edit_permission="brand_update",
            delete_permission="brand_delete"
        )

        self.add_btn.setText("+ Yeni Marka")
        self.refresh_data()

    def refresh_data(self):
        data = self.controller.brand_repo.get_all()
        self.set_data(data)

    def _render_table(self):
        super()._render_table()

        logo_col = None
        for i, col in enumerate(self.columns):
            if col["key"] == "logo_path":
                logo_col = i
                break

        if logo_col is not None:
            for row in range(self.table.rowCount()):
                item = self.filtered_data[row]
                logo_path = item.get("logo_path", "")

                container = QWidget()
                container.setStyleSheet("background: transparent; border: none;")
                container_layout = QHBoxLayout(container)
                container_layout.setContentsMargins(0, 0, 0, 0)
                container_layout.setAlignment(Qt.AlignCenter)

                logo_label = QLabel()
                logo_label.setFixedSize(32, 32)
                logo_label.setAlignment(Qt.AlignCenter)
                logo_label.setStyleSheet("background: transparent; border: none;")

                image_data = item.get("image_data", "")
                resolved = resolve_image_path(logo_path, image_data)
                if resolved:
                    pixmap = QPixmap(resolved)
                    if not pixmap.isNull():
                        scaled = pixmap.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        logo_label.setPixmap(scaled)
                    else:
                        logo_label.setText("🏷")
                else:
                    logo_label.setText("🏷")

                container_layout.addWidget(logo_label)
                self.table.setCellWidget(row, logo_col, container)

    def _on_add(self):
        dialog = BrandDialog(self)
        if dialog.exec_() == BrandDialog.Accepted:
            data = dialog.result_data
            result = self.controller.add_brand(
                name=data["name"],
                description=data.get("description", ""),
                logo_path=""
            )
            if result["success"]:
                brand_id = result.get("brand_id")
                source = data.get("logo_path", "")
                if source and brand_id:
                    rel_path, b64_data = save_entity_image(source, "brands", brand_id)
                    update = {"logo_path": rel_path}
                    if b64_data:
                        update["image_data"] = b64_data
                    self.controller.brand_repo.update(brand_id, update)
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _on_edit(self, item: dict):
        dialog = BrandDialog(self, edit_data=item)
        if dialog.exec_() == BrandDialog.Accepted:
            data = dialog.result_data
            update_data = {
                "name": data["name"],
                "description": data.get("description", ""),
            }

            logo_changed = data.get("_logo_changed", False)
            if logo_changed:
                source = data.get("logo_path", "")
                if source:
                    rel_path, b64_data = save_entity_image(source, "brands", item["ID"])
                    update_data["logo_path"] = rel_path
                    if b64_data:
                        update_data["image_data"] = b64_data
                else:
                    update_data["logo_path"] = ""
                    update_data["image_data"] = ""

            result = self.controller.update_brand(item["ID"], update_data)
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _on_delete(self, item: dict):
        name = item.get("name", "")
        if self.confirm_delete(name):
            result = self.controller.delete_brand(item["ID"])
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])


class BrandDialog(BaseDialog):
    def __init__(self, parent=None, edit_data: dict = None):
        self.edit_data = edit_data
        self._logo_changed = False

        if edit_data:
            stored_path = edit_data.get("logo_path", "")
            image_data = edit_data.get("image_data", "")
            self.selected_logo_path = resolve_image_path(stored_path, image_data) or ""
        else:
            self.selected_logo_path = ""

        title = "Marka Düzenle" if edit_data else "Yeni Marka Ekle"
        super().__init__(parent, title=title, width=480, height=450)

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

        select_logo_btn = QPushButton("📁 Logo Seç")
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
            QPushButton:hover {{
                background-color: #5bc7e0;
            }}
        """)
        select_logo_btn.clicked.connect(self._select_logo)
        logo_btn_inner.addWidget(select_logo_btn)

        clear_logo_btn = QPushButton("🗑️ Kaldır")
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
            QPushButton:hover {{
                background-color: #ff8a8a;
            }}
        """)
        clear_logo_btn.clicked.connect(self._clear_logo)
        logo_btn_inner.addWidget(clear_logo_btn)
        logo_btn_inner.addStretch()

        logo_layout.addWidget(logo_btn_layout)
        logo_layout.addStretch()

        self.form_layout.addWidget(logo_widget)

        self.add_form_separator()
        self.add_form_section_title("Genel Bilgiler")

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Marka adını girin")
        self.name_input.setStyleSheet(self._input_style())
        self.add_form_field("Marka Adı", self.name_input, required=True)

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Açıklama girin (opsiyonel)")
        self.desc_input.setStyleSheet(self._input_style())
        self.add_form_field("Açıklama", self.desc_input)

        if self.edit_data:
            self.name_input.setText(self.edit_data.get("name", ""))
            self.desc_input.setText(self.edit_data.get("description", ""))

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
        self.logo_preview.setText("🏷️")
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
            self.show_error("Marka adı boş bırakılamaz!")
            return

        self.result_data = {
            "name": name,
            "description": self.desc_input.text().strip(),
            "logo_path": self.selected_logo_path,
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
            QComboBox QAbstractItemView {{
                background-color: {Theme.BG_CARD};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                selection-background-color: {Theme.ACCENT};
            }}
        """