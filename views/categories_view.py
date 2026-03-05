from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QTreeWidget, QTreeWidgetItem,
                              QLineEdit, QTextEdit, QComboBox, QFrame,
                              QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from utils.theme import Theme
from utils.permission_helper import has_permission
from views.base_dialog import BaseDialog
from controllers.category_controller import CategoryController


class CategoriesView(QWidget):
    def __init__(self):
        super().__init__()
        self.controller = CategoryController()
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(15)

        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)

        tree_card = self._create_tree_card()
        content_layout.addWidget(tree_card, stretch=3)

        detail_card = self._create_detail_card()
        content_layout.addWidget(detail_card, stretch=2)

        layout.addLayout(content_layout)

    def _create_toolbar(self) -> QWidget:
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border-radius: {Theme.BORDER_RADIUS}px;
            }}
        """)

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 16px; background: transparent;")
        layout.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Kategori ara...")
        self.search_input.setFixedHeight(36)
        self.search_input.setFixedWidth(250)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 0 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid {Theme.BORDER_FOCUS};
            }}
        """)
        self.search_input.textChanged.connect(self._on_search)
        layout.addWidget(self.search_input)

        layout.addStretch()

        expand_btn = QPushButton("📂 Tümünü Aç")
        expand_btn.setCursor(Qt.PointingHandCursor)
        expand_btn.setFixedHeight(36)
        expand_btn.setStyleSheet(Theme.get_outline_button_style())
        expand_btn.clicked.connect(lambda: self.tree.expandAll())
        layout.addWidget(expand_btn)

        collapse_btn = QPushButton("📁 Tümünü Kapat")
        collapse_btn.setCursor(Qt.PointingHandCursor)
        collapse_btn.setFixedHeight(36)
        collapse_btn.setStyleSheet(Theme.get_outline_button_style())
        collapse_btn.clicked.connect(lambda: self.tree.collapseAll())
        layout.addWidget(collapse_btn)

        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setFixedHeight(36)
        refresh_btn.setStyleSheet(Theme.get_outline_button_style())
        refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_btn)

        if has_permission("category_create"):
            add_btn = QPushButton("+ Yeni Kategori")
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
                }}
                QPushButton:hover {{
                    background-color: {Theme.ACCENT_HOVER};
                }}
            """)
            add_btn.clicked.connect(self._on_add)
            layout.addWidget(add_btn)

        return toolbar

    def _create_tree_card(self) -> QWidget:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border-radius: {Theme.BORDER_RADIUS}px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        title = QLabel("📂 Kategori Ağacı")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(title)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Kategori", "Açıklama", "Alt Kategori", "ID"])
        self.tree.setColumnWidth(0, 250)
        self.tree.setColumnWidth(1, 200)
        self.tree.setColumnWidth(2, 80)
        self.tree.setColumnWidth(3, 50)
        self.tree.setAlternatingRowColors(True)
        self.tree.setAnimated(True)
        self.tree.itemClicked.connect(self._on_tree_item_clicked)

        self.tree.setStyleSheet(f"""
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
            QTreeWidget::item:alternate:selected {{
                background-color: {Theme.ACCENT};
                color: white;
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

        layout.addWidget(self.tree)

        self.tree_count_label = QLabel("Toplam: 0 kategori")
        self.tree_count_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px; background: transparent;")
        layout.addWidget(self.tree_count_label)

        return card

    def _create_detail_card(self) -> QWidget:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border-radius: {Theme.BORDER_RADIUS}px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("📋 Kategori Detayı")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {Theme.BORDER};")
        layout.addWidget(sep)

        self.detail_labels = {}

        fields = [
            ("ID", "ID"),
            ("Ad", "name"),
            ("Açıklama", "description"),
            ("Üst Kategori", "parent"),
            ("Alt Kategori Sayısı", "children_count"),
            ("Oluşturulma", "created_at"),
        ]

        for label_text, key in fields:
            row = QHBoxLayout()

            lbl = QLabel(f"{label_text}:")
            lbl.setFixedWidth(130)
            lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; font-weight: bold; background: transparent;")
            row.addWidget(lbl)

            value = QLabel("-")
            value.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 13px; background: transparent;")
            value.setWordWrap(True)
            row.addWidget(value)

            self.detail_labels[key] = value
            layout.addLayout(row)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        if has_permission("category_create"):
            self.add_child_btn = QPushButton("➕ Alt Kategori Ekle")
            self.add_child_btn.setCursor(Qt.PointingHandCursor)
            self.add_child_btn.setFixedHeight(34)
            self.add_child_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.INFO};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 0 12px;
                    font-size: 11px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background-color: #5bc7e0; }}
            """)
            self.add_child_btn.clicked.connect(self._on_add_child)
            self.add_child_btn.setEnabled(False)
            btn_layout.addWidget(self.add_child_btn)

        if has_permission("category_update"):
            self.edit_btn = QPushButton("✏️ Düzenle")
            self.edit_btn.setCursor(Qt.PointingHandCursor)
            self.edit_btn.setFixedHeight(34)
            self.edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.WARNING};
                    color: {Theme.TEXT_DARK};
                    border: none;
                    border-radius: 4px;
                    padding: 0 12px;
                    font-size: 11px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background-color: #ffe566; }}
            """)
            self.edit_btn.clicked.connect(self._on_edit)
            self.edit_btn.setEnabled(False)
            btn_layout.addWidget(self.edit_btn)

        if has_permission("category_delete"):
            self.delete_btn = QPushButton("🗑️ Sil")
            self.delete_btn.setCursor(Qt.PointingHandCursor)
            self.delete_btn.setFixedHeight(34)
            self.delete_btn.setStyleSheet(Theme.get_danger_button_style())
            self.delete_btn.clicked.connect(self._on_delete)
            self.delete_btn.setEnabled(False)
            btn_layout.addWidget(self.delete_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return card


    def refresh_data(self):
        self.all_categories = self.controller.category_repo.get_all()
        self._build_tree(self.all_categories)
        self.tree_count_label.setText(f"Toplam: {len(self.all_categories)} kategori")
        self._clear_detail()

    def _build_tree(self, categories: list[dict], filter_text: str = ""):
        self.tree.clear()
        cat_map = {}

        if filter_text:
            filtered_ids = set()
            for cat in categories:
                if filter_text.lower() in cat.get("name", "").lower():
                    filtered_ids.add(cat["ID"])
                    parent_id = cat.get("parent_category_ID")
                    while parent_id:
                        filtered_ids.add(parent_id)
                        parent = next((c for c in categories if c["ID"] == parent_id), None)
                        parent_id = parent.get("parent_category_ID") if parent else None
            categories = [c for c in categories if c["ID"] in filtered_ids]

        for cat in categories:
            children_count = len([c for c in self.all_categories
                                  if c.get("parent_category_ID") == cat["ID"]])

            item = QTreeWidgetItem()
            item.setText(0, f"📁 {cat.get('name', '')}")
            item.setText(1, cat.get("description", "") or "-")
            item.setText(2, str(children_count))
            item.setText(3, str(cat["ID"]))
            item.setData(0, Qt.UserRole, cat)

            cat_map[cat["ID"]] = item

        for cat in categories:
            item = cat_map[cat["ID"]]
            parent_id = cat.get("parent_category_ID")

            if parent_id and parent_id in cat_map:
                cat_map[parent_id].addChild(item)
            else:
                self.tree.addTopLevelItem(item)

        self.tree.expandAll()

    def _on_search(self, text: str):
        self._build_tree(self.all_categories, text.strip())

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        cat = item.data(0, Qt.UserRole)
        if not cat:
            return

        self.selected_category = cat

        self.detail_labels["ID"].setText(str(cat.get("ID", "")))
        self.detail_labels["name"].setText(cat.get("name", ""))
        self.detail_labels["description"].setText(cat.get("description", "") or "-")
        self.detail_labels["created_at"].setText(cat.get("created_at", "")[:19])

        parent_id = cat.get("parent_category_ID")
        if parent_id:
            parent = next((c for c in self.all_categories if c["ID"] == parent_id), None)
            self.detail_labels["parent"].setText(parent.get("name", "?") if parent else "-")
        else:
            self.detail_labels["parent"].setText("Ana Kategori (Kök)")

        children = [c for c in self.all_categories if c.get("parent_category_ID") == cat["ID"]]
        self.detail_labels["children_count"].setText(str(len(children)))

        if hasattr(self, 'add_child_btn'):
            self.add_child_btn.setEnabled(True)
        if hasattr(self, 'edit_btn'):
            self.edit_btn.setEnabled(True)
        if hasattr(self, 'delete_btn'):
            self.delete_btn.setEnabled(True)

    def _clear_detail(self):
        self.selected_category = None
        for label in self.detail_labels.values():
            label.setText("-")
        if hasattr(self, 'add_child_btn'):
            self.add_child_btn.setEnabled(False)
        if hasattr(self, 'edit_btn'):
            self.edit_btn.setEnabled(False)
        if hasattr(self, 'delete_btn'):
            self.delete_btn.setEnabled(False)


    def _on_add(self):
        dialog = CategoryDialog(self, categories=self.all_categories)
        if dialog.exec_() == CategoryDialog.Accepted:
            data = dialog.result_data
            result = self.controller.add_category(
                name=data["name"],
                description=data.get("description", ""),
                parent_id=data.get("parent_category_ID")
            )
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _on_add_child(self):
        if not self.selected_category:
            return
        dialog = CategoryDialog(self, categories=self.all_categories,
                                 default_parent_id=self.selected_category["ID"])
        if dialog.exec_() == CategoryDialog.Accepted:
            data = dialog.result_data
            result = self.controller.add_category(
                name=data["name"],
                description=data.get("description", ""),
                parent_id=data.get("parent_category_ID")
            )
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _on_edit(self):
        if not self.selected_category:
            return
        dialog = CategoryDialog(self, categories=self.all_categories,
                                 edit_data=self.selected_category)
        if dialog.exec_() == CategoryDialog.Accepted:
            data = dialog.result_data
            result = self.controller.update_category(self.selected_category["ID"], data)
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _on_delete(self):
        if not self.selected_category:
            return
        name = self.selected_category.get("name", "")
        reply = QMessageBox.question(
            self, "Silme Onayı",
            f"'{name}' kategorisini silmek istediğinize emin misiniz?\n\nAlt kategoriler de silinecektir!",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            result = self.controller.delete_category(self.selected_category["ID"])
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])


class CategoryDialog(BaseDialog):
    def __init__(self, parent=None, categories: list = None,
                 edit_data: dict = None, default_parent_id: int = None):
        self.categories = categories or []
        self.edit_data = edit_data
        self.default_parent_id = default_parent_id

        title = "Kategori Düzenle" if edit_data else "Yeni Kategori Ekle"
        super().__init__(parent, title=title, width=450, height=350)

    def _setup_form(self):
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Kategori adını girin")
        self.name_input.setStyleSheet(self._input_style())
        self.add_form_field("Kategori Adı", self.name_input, required=True)

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Açıklama girin (opsiyonel)")
        self.desc_input.setStyleSheet(self._input_style())
        self.add_form_field("Açıklama", self.desc_input)

        self.parent_combo = QComboBox()
        self.parent_combo.setStyleSheet(self._input_style())
        self.parent_combo.addItem("-- Ana Kategori (Kök) --", None)

        current_id = self.edit_data["ID"] if self.edit_data else None
        self._populate_parent_combo(self.categories, current_id)

        self.add_form_field("Üst Kategori", self.parent_combo)

        if self.edit_data:
            self.name_input.setText(self.edit_data.get("name", ""))
            self.desc_input.setText(self.edit_data.get("description", ""))

            parent_id = self.edit_data.get("parent_category_ID")
            if parent_id:
                index = self.parent_combo.findData(parent_id)
                if index >= 0:
                    self.parent_combo.setCurrentIndex(index)

        if self.default_parent_id:
            index = self.parent_combo.findData(self.default_parent_id)
            if index >= 0:
                self.parent_combo.setCurrentIndex(index)

        self.form_layout.addStretch()

    def _populate_parent_combo(self, categories: list, exclude_id: int = None,
                                 parent_id=None, prefix: str = ""):
        for cat in categories:
            if cat.get("parent_category_ID") == parent_id:
                if exclude_id and cat["ID"] == exclude_id:
                    continue
                self.parent_combo.addItem(f"{prefix}{cat['name']}", cat["ID"])
                self._populate_parent_combo(categories, exclude_id,
                                             cat["ID"], prefix + "  ├─ ")

    def _on_save(self):
        name = self.name_input.text().strip()
        if not name:
            self.show_error("Kategori adı boş bırakılamaz!")
            return

        self.result_data = {
            "name": name,
            "description": self.desc_input.text().strip(),
            "parent_category_ID": self.parent_combo.currentData(),
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