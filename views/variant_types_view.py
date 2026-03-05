from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QTreeWidget,
                              QTreeWidgetItem, QHeaderView,
                              QMessageBox, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from views.base_dialog import BaseDialog
from controllers.variant_type_controller import VariantTypeController
from utils.theme import Theme
from utils.permission_helper import has_permission


class VariantTypesView(QWidget):
    def __init__(self):
        super().__init__()
        self.controller = VariantTypeController()
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(15)

        title_label = QLabel("🏷️ Varyant Tipleri Yönetimi")
        title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        layout.addWidget(title_label)

        layout.addWidget(self._create_toolbar())

        self.tree = self._create_tree()
        layout.addWidget(self.tree)

        self.footer_label = QLabel("Toplam: 0 tip")
        self.footer_label.setStyleSheet(f"""
            color: {Theme.TEXT_SECONDARY};
            font-size: 12px;
            padding: 8px 15px;
            background-color: {Theme.BG_CARD};
            border-radius: 6px;
        """)
        self.footer_label.setFixedHeight(36)
        layout.addWidget(self.footer_label)

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
        self.search_input.setPlaceholderText("Varyant tipi ara...")
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
            QLineEdit:focus {{ border: 1px solid {Theme.BORDER_FOCUS}; }}
        """)
        self.search_input.textChanged.connect(self._on_search)
        layout.addWidget(self.search_input)

        layout.addStretch()

        expand_btn = QPushButton("Tümünü Aç")
        expand_btn.setCursor(Qt.PointingHandCursor)
        expand_btn.setFixedHeight(36)
        expand_btn.setStyleSheet(Theme.get_outline_button_style())
        expand_btn.clicked.connect(lambda: self.tree.expandAll())
        layout.addWidget(expand_btn)

        collapse_btn = QPushButton("Tümünü Kapat")
        collapse_btn.setCursor(Qt.PointingHandCursor)
        collapse_btn.setFixedHeight(36)
        collapse_btn.setStyleSheet(Theme.get_outline_button_style())
        collapse_btn.clicked.connect(lambda: self.tree.collapseAll())
        layout.addWidget(collapse_btn)

        refresh_btn = QPushButton("Yenile")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setFixedHeight(36)
        refresh_btn.setStyleSheet(Theme.get_outline_button_style())
        refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_btn)

        add_btn = QPushButton("+ Yeni Tip")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setFixedHeight(36)
        add_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: {Theme.ACCENT_HOVER}; }}
        """)
        add_btn.clicked.connect(self._on_add_type)
        if not has_permission("variant_type_create"):
            add_btn.setVisible(False)
        layout.addWidget(add_btn)

        return toolbar

    def _create_tree(self) -> QTreeWidget:
        tree = QTreeWidget()
        tree.setColumnCount(4)
        tree.setHeaderLabels(["Ad", "Değer Sayısı", "ID", "İşlemler"])

        tree.setAlternatingRowColors(True)
        tree.setRootIsDecorated(True)
        tree.setAnimated(True)
        tree.setExpandsOnDoubleClick(True)
        tree.setSelectionBehavior(QTreeWidget.SelectRows)
        tree.setUniformRowHeights(True)

        header = tree.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.resizeSection(1, 100)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.resizeSection(2, 60)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.resizeSection(3, 180)

        tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {Theme.BG_DARK};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                outline: none;
                alternate-background-color: rgba(255, 255, 255, 0.03);
            }}
            QTreeWidget::item {{
                padding: 8px 5px;
                border-bottom: 1px solid {Theme.BORDER};
                color: {Theme.TEXT_PRIMARY};
            }}
            QTreeWidget::item:selected {{
                background-color: {Theme.ACCENT};
                color: white;
            }}
            QTreeWidget::item:hover {{
                background-color: {Theme.BG_HOVER};
                color: {Theme.TEXT_PRIMARY};
            }}
            QTreeWidget::item:alternate {{
                background-color: rgba(255, 255, 255, 0.03);
                color: {Theme.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {Theme.BG_SIDEBAR};
                color: {Theme.TEXT_PRIMARY};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {Theme.ACCENT};
                font-weight: bold;
            }}
            QTreeWidget::branch {{
                background-color: transparent;
            }}
        """)

        return tree


    def refresh_data(self):
        self.tree.clear()
        result = self.controller.get_all_types_with_values()
        types = result.get("data", [])

        for variant_type in types:
            self._add_type_item(variant_type)

        self.tree.expandAll()
        self.footer_label.setText(f"Toplam: {len(types)} tip")

    def _add_type_item(self, variant_type: dict):
        from PyQt5.QtCore import QSize

        type_item = QTreeWidgetItem(self.tree)
        type_item.setText(0, f"🏷️ {variant_type['name']}")
        values = variant_type.get("values", [])
        type_item.setText(1, str(len(values)))
        type_item.setTextAlignment(1, Qt.AlignCenter)
        type_item.setText(2, str(variant_type["ID"]))
        type_item.setTextAlignment(2, Qt.AlignCenter)
        type_item.setData(0, Qt.UserRole, {"kind": "type", "data": variant_type})
        type_item.setSizeHint(0, QSize(0, 40))

        self._create_type_buttons(type_item, variant_type)

        for value in values:
            self._add_value_item(type_item, value, variant_type)

    def _add_value_item(self, parent_item: QTreeWidgetItem, value: dict, variant_type: dict):
        from PyQt5.QtCore import QSize

        value_item = QTreeWidgetItem(parent_item)
        value_item.setText(0, f"   └─ {value['value']}")
        value_item.setText(1, "")
        value_item.setText(2, str(value["ID"]))
        value_item.setTextAlignment(2, Qt.AlignCenter)
        value_item.setData(0, Qt.UserRole, {"kind": "value", "data": value, "type": variant_type})
        value_item.setSizeHint(0, QSize(0, 40))
        value_item.setForeground(0, __import__('PyQt5.QtGui', fromlist=['QColor']).QColor(Theme.TEXT_SECONDARY))

        self._create_value_buttons(value_item, value, variant_type)

    def _create_type_buttons(self, tree_item: QTreeWidgetItem, data: dict):
        actions_widget = QWidget()
        actions_widget.setStyleSheet("background: transparent;")
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(6, 4, 6, 4)
        actions_layout.setSpacing(6)
        actions_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        def make_btn(text, tooltip, color, hover, callback):
            btn = QPushButton(text)
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(28)
            btn.setMinimumWidth(50)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0 10px;
                }}
                QPushButton:hover {{ background-color: {hover}; }}
            """)
            btn.clicked.connect(callback)
            return btn

        if has_permission("variant_type_create"):
            actions_layout.addWidget(make_btn(
                "+ Değer", "Değer ekle",
                Theme.SUCCESS, "#66bb6a",
                lambda checked, d=data: self._on_add_value(d)
            ))

        if has_permission("variant_type_update"):
            actions_layout.addWidget(make_btn(
                "Düzenle", "Düzenle",
                Theme.INFO, "#5bc7e0",
                lambda checked, d=data: self._on_edit_type(d)
            ))

        if has_permission("variant_type_delete"):
            actions_layout.addWidget(make_btn(
                "Sil", "Sil",
                Theme.ERROR, "#ff8a8a",
                lambda checked, d=data: self._on_delete_type(d)
            ))

        self.tree.setItemWidget(tree_item, 3, actions_widget)

    def _create_value_buttons(self, tree_item: QTreeWidgetItem, value: dict, variant_type: dict):
        actions_widget = QWidget()
        actions_widget.setStyleSheet("background: transparent;")
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(6, 4, 6, 4)
        actions_layout.setSpacing(6)
        actions_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        def make_btn(text, tooltip, color, hover, callback):
            btn = QPushButton(text)
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(28)
            btn.setMinimumWidth(50)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0 10px;
                }}
                QPushButton:hover {{ background-color: {hover}; }}
            """)
            btn.clicked.connect(callback)
            return btn

        if has_permission("variant_type_update"):
            actions_layout.addWidget(make_btn(
                "Düzenle", "Düzenle",
                Theme.INFO, "#5bc7e0",
                lambda checked, v=value, t=variant_type: self._on_edit_value(v, t)
            ))

        if has_permission("variant_type_delete"):
            actions_layout.addWidget(make_btn(
                "Sil", "Sil",
                Theme.ERROR, "#ff8a8a",
                lambda checked, v=value: self._on_delete_value(v)
            ))

        self.tree.setItemWidget(tree_item, 3, actions_widget)


    def _on_add_type(self):
        dialog = VariantTypeDialog(self)
        if dialog.exec_() == VariantTypeDialog.Accepted:
            result = self.controller.add_variant_type(dialog.result_data["name"])
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _on_edit_type(self, data: dict):
        dialog = VariantTypeDialog(self, edit_data=data)
        if dialog.exec_() == VariantTypeDialog.Accepted:
            result = self.controller.update_variant_type(
                data["ID"], {"name": dialog.result_data["name"]}
            )
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _on_delete_type(self, data: dict):
        reply = QMessageBox.question(
            self, "Silme Onayı",
            f"'{data['name']}' tipini silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            result = self.controller.delete_variant_type(data["ID"])
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _on_add_value(self, variant_type: dict):
        dialog = VariantValueDialog(self, variant_type=variant_type)
        if dialog.exec_() == VariantValueDialog.Accepted:
            result = self.controller.add_variant_value(
                variant_type["ID"], dialog.result_data["value"]
            )
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _on_edit_value(self, value: dict, variant_type: dict):
        dialog = VariantValueDialog(self, variant_type=variant_type, edit_data=value)
        if dialog.exec_() == VariantValueDialog.Accepted:
            result = self.controller.update_variant_value(
                value["ID"], dialog.result_data["value"]
            )
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _on_delete_value(self, value: dict):
        reply = QMessageBox.question(
            self, "Silme Onayı",
            f"'{value['value']}' değerini silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            result = self.controller.delete_variant_value(value["ID"])
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _on_search(self, text: str):
        if not text.strip():
            self.refresh_data()
            return

        text_lower = text.lower()
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            type_item = root.child(i)
            type_name = type_item.text(0).lower()
            type_match = text_lower in type_name

            value_match = False
            for j in range(type_item.childCount()):
                value_item = type_item.child(j)
                value_name = value_item.text(0).lower()
                match = text_lower in value_name
                value_item.setHidden(not match and not type_match)
                if match:
                    value_match = True

            type_item.setHidden(not type_match and not value_match)
            if value_match:
                type_item.setExpanded(True)


class VariantTypeDialog(BaseDialog):
    def __init__(self, parent=None, edit_data: dict = None):
        self.edit_data = edit_data
        title = "Tip Düzenle" if edit_data else "Yeni Varyant Tipi"
        super().__init__(parent, title=title, width=400, height=250)

    def _setup_form(self):
        self.add_form_section_title("Tip Bilgisi")

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("ör: Renk, Beden, Materyal...")
        self.name_input.setStyleSheet(self._input_style())
        self.add_form_field("Tip Adı", self.name_input, required=True)

        if self.edit_data:
            self.name_input.setText(self.edit_data.get("name", ""))

        self.form_layout.addStretch()

    def _on_save(self):
        name = self.name_input.text().strip()
        if not name:
            self.show_error("Tip adı boş bırakılamaz!")
            return
        self.result_data = {"name": name}
        self.accept()

    def _input_style(self) -> str:
        return f"""
            QLineEdit {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{ border: 1px solid {Theme.BORDER_FOCUS}; }}
        """


class VariantValueDialog(BaseDialog):
    def __init__(self, parent=None, variant_type: dict = None, edit_data: dict = None):
        self.variant_type = variant_type
        self.edit_data = edit_data
        title = "Değer Düzenle" if edit_data else "Yeni Değer Ekle"
        super().__init__(parent, title=title, width=400, height=270)

    def _setup_form(self):
        type_name = self.variant_type.get("name", "") if self.variant_type else ""
        self.add_form_section_title(f"Tip: {type_name}")

        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("ör: Kırmızı, XL, Pamuk...")
        self.value_input.setStyleSheet(self._input_style())
        self.add_form_field("Değer", self.value_input, required=True)

        if self.edit_data:
            self.value_input.setText(self.edit_data.get("value", ""))

        self.form_layout.addStretch()

    def _on_save(self):
        value = self.value_input.text().strip()
        if not value:
            self.show_error("Değer boş bırakılamaz!")
            return
        self.result_data = {"value": value}
        self.accept()

    def _input_style(self) -> str:
        return f"""
            QLineEdit {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{ border: 1px solid {Theme.BORDER_FOCUS}; }}
        """