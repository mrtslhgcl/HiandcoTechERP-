from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QTreeWidget,
                              QTreeWidgetItem, QHeaderView, QComboBox,
                              QMessageBox, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from views.base_dialog import BaseDialog
from controllers.location_controller import LocationController
from utils.theme import Theme
from utils.permission_helper import has_permission


class LocationsView(QWidget):
    def __init__(self):
        super().__init__()
        self.controller = LocationController()
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(15)

        title_label = QLabel("📍 Lokasyon Yönetimi")
        title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        layout.addWidget(title_label)

        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        self.tree = self._create_tree()
        layout.addWidget(self.tree)

        self.footer_label = QLabel("Toplam: 0 lokasyon")
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
        self.search_input.setPlaceholderText("Lokasyon ara...")
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

        if has_permission("location_create"):
            add_btn = QPushButton("+ Yeni Lokasyon")
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
            add_btn.clicked.connect(lambda: self._on_add(None))
            layout.addWidget(add_btn)

        return toolbar

    def _create_tree(self) -> QTreeWidget:
        tree = QTreeWidget()
        tree.setColumnCount(5)
        tree.setHeaderLabels(["Lokasyon", "Açıklama", "Alt Lokasyon", "ID", "İşlemler"])

        tree.setAlternatingRowColors(True)
        tree.setRootIsDecorated(True)
        tree.setAnimated(True)
        tree.setExpandsOnDoubleClick(True)
        tree.setSelectionBehavior(QTreeWidget.SelectRows)
        tree.setUniformRowHeights(True)
        tree.setIconSize(__import__('PyQt5.QtCore', fromlist=['QSize']).QSize(16, 16))

        header = tree.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.resizeSection(2, 100)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.resizeSection(3, 60)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.resizeSection(4, 180)

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
        tree_data = self.controller.get_location_tree()
        total = self._count_all(tree_data)
        self._populate_tree(tree_data, self.tree.invisibleRootItem())
        self.tree.expandAll()
        self.footer_label.setText(f"Toplam: {total} lokasyon")

    def _count_all(self, nodes: list[dict]) -> int:
        count = len(nodes)
        for node in nodes:
            count += self._count_all(node.get("children", []))
        return count

    def _populate_tree(self, nodes: list[dict], parent_item):
        for node in nodes:
            item = QTreeWidgetItem(parent_item)
            item.setText(0, f"📍 {node['name']}")
            item.setText(1, node.get("description", "") or "-")

            children = node.get("children", [])
            item.setText(2, str(len(children)))
            item.setTextAlignment(2, Qt.AlignCenter)

            item.setText(3, str(node["ID"]))
            item.setTextAlignment(3, Qt.AlignCenter)

            item.setData(0, Qt.UserRole, node)

            item.setSizeHint(0, __import__('PyQt5.QtCore', fromlist=['QSize']).QSize(0, 40))

            self._create_action_buttons(item, node)

            if children:
                self._populate_tree(children, item)

    def _create_action_buttons(self, tree_item: QTreeWidgetItem, data: dict):
        from PyQt5.QtCore import QSize

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
                QPushButton:hover {{
                    background-color: {hover};
                }}
            """)
            btn.clicked.connect(callback)
            return btn

        if has_permission("location_create"):
            actions_layout.addWidget(make_btn(
                "+ Alt", "Alt lokasyon ekle",
                Theme.SUCCESS, "#66bb6a",
                lambda checked, d=data: self._on_add(d["ID"])
            ))

        if has_permission("location_update"):
            actions_layout.addWidget(make_btn(
                "Düzenle", "Düzenle",
                Theme.INFO, "#5bc7e0",
                lambda checked, d=data: self._on_edit(d)
            ))

        if has_permission("location_delete"):
            actions_layout.addWidget(make_btn(
                "Sil", "Sil",
                Theme.ERROR, "#ff8a8a",
                lambda checked, d=data: self._on_delete(d)
            ))

        self.tree.setItemWidget(tree_item, 4, actions_widget)

    def _on_add(self, parent_id=None):
        all_locations = self.controller.location_repo.get_all()
        dialog = LocationDialog(self, all_locations=all_locations, parent_id=parent_id)

        if dialog.exec_() == LocationDialog.Accepted:
            data = dialog.result_data
            result = self.controller.add_location(
                name=data["name"],
                parent_location_ID=data.get("parent_location_ID"),
                description=data.get("description", "")
            )
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _on_edit(self, item: dict):
        all_locations = self.controller.location_repo.get_all()
        dialog = LocationDialog(self, edit_data=item, all_locations=all_locations)

        if dialog.exec_() == LocationDialog.Accepted:
            data = dialog.result_data
            update_data = {
                "name": data["name"],
                "parent_location_ID": data.get("parent_location_ID"),
                "description": data.get("description", ""),
            }
            result = self.controller.update_location(item["ID"], update_data)
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _on_delete(self, item: dict):
        children = item.get("children", [])
        if children:
            QMessageBox.warning(self, "Uyarı",
                                f"'{item['name']}' altında {len(children)} alt lokasyon var.\nÖnce alt lokasyonları silin.")
            return

        reply = QMessageBox.question(
            self, "Silme Onayı",
            f"'{item['name']}' lokasyonunu silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            result = self.controller.delete_location(item["ID"])
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
        self._filter_tree_items(root, text_lower)

    def _filter_tree_items(self, parent_item, search_text: str) -> bool:
        any_visible = False
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            name = child.text(0).lower()
            desc = child.text(1).lower()

            child_visible = self._filter_tree_items(child, search_text)
            self_match = search_text in name or search_text in desc

            visible = self_match or child_visible
            child.setHidden(not visible)

            if visible:
                any_visible = True
                if child_visible:
                    child.setExpanded(True)

        return any_visible


class LocationDialog(BaseDialog):
    def __init__(self, parent=None, edit_data: dict = None,
                 all_locations: list[dict] = None, parent_id: int = None):
        self.edit_data = edit_data
        self.all_locations = all_locations or []
        self.initial_parent_id = parent_id
        title = "Lokasyon Düzenle" if edit_data else "Yeni Lokasyon Ekle"
        super().__init__(parent, title=title, width=460, height=350)

    def _setup_form(self):
        self.add_form_section_title("Lokasyon Bilgileri")

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Lokasyon adını girin")
        self.name_input.setStyleSheet(self._input_style())
        self.add_form_field("Lokasyon Adı", self.name_input, required=True)

        self.parent_combo = QComboBox()
        self.parent_combo.setStyleSheet(self._input_style())
        self.parent_combo.addItem("-- Ana Lokasyon (Kök) --", None)

        exclude_ids = set()
        if self.edit_data:
            exclude_ids.add(self.edit_data["ID"])
            for loc in self.all_locations:
                if self._is_descendant(loc["ID"], self.edit_data["ID"]):
                    exclude_ids.add(loc["ID"])

        for loc in self.all_locations:
            if loc["ID"] not in exclude_ids:
                depth = self._get_depth(loc)
                prefix = "  " * depth + ("└─ " if depth > 0 else "")
                self.parent_combo.addItem(f"{prefix}📍 {loc['name']}", loc["ID"])

        self.add_form_field("Üst Lokasyon", self.parent_combo)

        if self.edit_data:
            parent_id = self.edit_data.get("parent_location_ID")
            index = self.parent_combo.findData(parent_id)
            if index >= 0:
                self.parent_combo.setCurrentIndex(index)
        elif self.initial_parent_id is not None:
            index = self.parent_combo.findData(self.initial_parent_id)
            if index >= 0:
                self.parent_combo.setCurrentIndex(index)

        self.add_form_separator()

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Açıklama (opsiyonel)")
        self.desc_input.setStyleSheet(self._input_style())
        self.add_form_field("Açıklama", self.desc_input)

        if self.edit_data:
            self.name_input.setText(self.edit_data.get("name", ""))
            self.desc_input.setText(self.edit_data.get("description", ""))

        self.form_layout.addStretch()

    def _get_depth(self, location: dict) -> int:
        depth = 0
        parent_id = location.get("parent_location_ID")
        visited = set()
        while parent_id is not None:
            if parent_id in visited:
                break
            visited.add(parent_id)
            parent = None
            for loc in self.all_locations:
                if loc["ID"] == parent_id:
                    parent = loc
                    break
            if parent is None:
                break
            depth += 1
            parent_id = parent.get("parent_location_ID")
        return depth

    def _is_descendant(self, loc_id: int, ancestor_id: int) -> bool:
        visited = set()
        current_id = loc_id
        while current_id is not None:
            if current_id in visited:
                return False
            visited.add(current_id)
            parent = None
            for loc in self.all_locations:
                if loc["ID"] == current_id:
                    parent = loc
                    break
            if parent is None:
                return False
            if parent.get("parent_location_ID") == ancestor_id:
                return True
            current_id = parent.get("parent_location_ID")
        return False

    def _on_save(self):
        name = self.name_input.text().strip()
        if not name:
            self.show_error("Lokasyon adı boş bırakılamaz!")
            return

        self.result_data = {
            "name": name,
            "parent_location_ID": self.parent_combo.currentData(),
            "description": self.desc_input.text().strip(),
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