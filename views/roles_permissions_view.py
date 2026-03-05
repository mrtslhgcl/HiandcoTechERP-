import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFrame,
    QComboBox, QTabWidget, QAbstractItemView, QCheckBox, QScrollArea,
    QGridLayout, QSizePolicy, QSpinBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from views.base_dialog import BaseDialog
from controllers.role_permissions_controller import RolePermissionController
from database.employee_role_repository import EmployeeRoleRepository
from utils.theme import Theme
from utils.permission_helper import has_permission
import math


PERMISSION_GROUPS = {
    "Kategori": ["category_create", "category_update", "category_delete"],
    "Marka": ["brand_create", "brand_update", "brand_delete"],
    "Tedarikçi": ["supplier_create", "supplier_update", "supplier_delete"],
    "Lokasyon": ["location_create", "location_update", "location_delete"],
    "Varyant Tipi": ["variant_type_create", "variant_type_update", "variant_type_delete"],
    "Ürün": ["product_create", "product_update", "product_delete"],
    "Stok": ["stock_create", "stock_update", "stock_delete"],
    "Müşteri": ["customer_create", "customer_update", "customer_delete"],
    "Sipariş": ["order_create", "order_update", "order_delete", "order_cancel", "order_refund", "payment_manage"],
    "Çalışan": ["employee_create", "employee_update", "employee_delete"],
    "Kullanıcı": ["user_manage", "user_reset_password"],
    "Rol & Yetki": ["role_manage", "role_assign", "permission_manage"],
}

PERMISSION_LABELS = {
    "category_create": "Ekleme", "category_update": "Güncelleme", "category_delete": "Silme",
    "brand_create": "Ekleme", "brand_update": "Güncelleme", "brand_delete": "Silme",
    "supplier_create": "Ekleme", "supplier_update": "Güncelleme", "supplier_delete": "Silme",
    "location_create": "Ekleme", "location_update": "Güncelleme", "location_delete": "Silme",
    "variant_type_create": "Ekleme", "variant_type_update": "Güncelleme", "variant_type_delete": "Silme",
    "product_create": "Ekleme", "product_update": "Güncelleme", "product_delete": "Silme",
    "stock_create": "Ekleme", "stock_update": "Güncelleme", "stock_delete": "Silme",
    "customer_create": "Ekleme", "customer_update": "Güncelleme", "customer_delete": "Silme",
    "order_create": "Oluşturma", "order_update": "Güncelleme", "order_delete": "Silme",
    "order_cancel": "İptal", "order_refund": "İade", "payment_manage": "Ödeme Yönetimi",
    "employee_create": "Ekleme", "employee_update": "Güncelleme", "employee_delete": "Silme",
    "user_manage": "Hesap Yönetimi", "user_reset_password": "Şifre Sıfırlama",
    "role_manage": "Rol Yönetimi", "role_assign": "Rol Atama", "permission_manage": "Yetki Yönetimi",
}


def _input_style():
    return f"""
        QLineEdit, QSpinBox, QDoubleSpinBox {{
            background-color: {Theme.BG_INPUT};
            color: {Theme.TEXT_PRIMARY};
            border: 1px solid {Theme.BORDER};
            border-radius: {Theme.BORDER_RADIUS_SMALL}px;
            padding: 8px 12px;
            font-size: {Theme.FONT_SIZE_NORMAL}px;
        }}
        QLineEdit:focus, QSpinBox:focus {{
            border-color: {Theme.BORDER_FOCUS};
        }}
    """


def _table_style():
    return f"""
        QTableWidget {{
            background-color: {Theme.BG_DARK};
            color: {Theme.TEXT_PRIMARY};
            border: 1px solid {Theme.BORDER};
            gridline-color: {Theme.BORDER};
            selection-background-color: {Theme.BG_HOVER};
        }}
        QTableWidget::item {{
            color: {Theme.TEXT_PRIMARY};
            padding: 4px 8px;
        }}
        QHeaderView::section {{
            background-color: {Theme.BG_SIDEBAR};
            color: {Theme.TEXT_PRIMARY};
            border: 1px solid {Theme.BORDER};
            padding: 8px;
            font-weight: bold;
        }}
    """


class RolesPermissionsView(QWidget):
    def __init__(self):
        super().__init__()
        self.controller = RolePermissionController()
        self.employee_role_repo = EmployeeRoleRepository()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("🔐 Roller & Yetkiler")
        title.setFont(QFont(Theme.FONT_FAMILY, Theme.FONT_SIZE_TITLE, QFont.Bold))
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        layout.addWidget(title)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {Theme.BORDER};
                background-color: {Theme.BG_DARK};
                border-radius: 8px;
            }}
            QTabBar::tab {{
                background-color: {Theme.BG_SIDEBAR};
                color: {Theme.TEXT_SECONDARY};
                min-width: 160px;
                padding: 10px 20px;
                border: 1px solid {Theme.BORDER};
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                background-color: {Theme.BG_DARK};
                color: {Theme.TEXT_PRIMARY};
                border-bottom: 2px solid {Theme.ACCENT};
            }}
            QTabBar::tab:hover {{
                background-color: {Theme.BG_HOVER};
            }}
        """)

        self.tabs.addTab(self._build_roles_tab(), "🛡️ Roller")
        self.tabs.addTab(self._build_permissions_tab(), "🔑 Yetkiler")
        layout.addWidget(self.tabs)


    def _build_roles_tab(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        left_panel = QFrame()
        left_panel.setFixedWidth(340)
        left_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border-radius: 8px;
                border: 1px solid {Theme.BORDER};
            }}
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        header_w = QWidget()
        header_w.setStyleSheet("background: transparent;")
        header_l = QHBoxLayout(header_w)
        header_l.setContentsMargins(0, 0, 0, 0)
        header_l.setSpacing(8)

        roles_title = QLabel("Roller")
        roles_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        roles_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; background: transparent;")
        header_l.addWidget(roles_title)
        header_l.addStretch()

        if has_permission("role_manage"):
            add_role_btn = QPushButton("+ Yeni Rol")
            add_role_btn.setCursor(Qt.PointingHandCursor)
            add_role_btn.setFixedHeight(32)
            add_role_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.SUCCESS};
                    color: {Theme.TEXT_DARK};
                    border: none; border-radius: 6px;
                    font-weight: bold; font-size: 11px;
                    padding: 0 14px;
                }}
                QPushButton:hover {{ background-color: #5fddb5; }}
            """)
            add_role_btn.clicked.connect(self._on_add_role)
            header_l.addWidget(add_role_btn)

        left_layout.addWidget(header_w)

        self.roles_table = QTableWidget()
        self.roles_table.setColumnCount(3)
        self.roles_table.setHorizontalHeaderLabels(["Rol Adı", "Açıklama", "Yetki"])
        self.roles_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.roles_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.roles_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.roles_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.roles_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.roles_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.roles_table.verticalHeader().setVisible(False)
        self.roles_table.setStyleSheet(_table_style())
        self.roles_table.clicked.connect(self._on_role_selected)
        left_layout.addWidget(self.roles_table)

        if has_permission("role_manage"):
            btn_w = QWidget()
            btn_w.setStyleSheet("background: transparent;")
            btn_l = QHBoxLayout(btn_w)
            btn_l.setContentsMargins(0, 0, 0, 0)
            btn_l.setSpacing(8)

            self.edit_role_btn = QPushButton("Düzenle")
            self.edit_role_btn.setCursor(Qt.PointingHandCursor)
            self.edit_role_btn.setFixedHeight(32)
            self.edit_role_btn.setEnabled(False)
            self.edit_role_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.INFO};
                    color: white; border: none; border-radius: 6px;
                    font-weight: bold; font-size: 11px; padding: 0 14px;
                }}
                QPushButton:hover {{ background-color: #5bc7e0; }}
                QPushButton:disabled {{ background-color: {Theme.TEXT_MUTED}; color: {Theme.BG_DARK}; }}
            """)
            self.edit_role_btn.clicked.connect(self._on_edit_role)
            btn_l.addWidget(self.edit_role_btn)

            self.delete_role_btn = QPushButton("Sil")
            self.delete_role_btn.setCursor(Qt.PointingHandCursor)
            self.delete_role_btn.setFixedHeight(32)
            self.delete_role_btn.setEnabled(False)
            self.delete_role_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.ERROR};
                    color: white; border: none; border-radius: 6px;
                    font-weight: bold; font-size: 11px; padding: 0 14px;
                }}
                QPushButton:hover {{ background-color: #ff8a8a; }}
                QPushButton:disabled {{ background-color: {Theme.TEXT_MUTED}; color: {Theme.BG_DARK}; }}
            """)
            self.delete_role_btn.clicked.connect(self._on_delete_role)
            btn_l.addWidget(self.delete_role_btn)

            btn_l.addStretch()
            left_layout.addWidget(btn_w)

        layout.addWidget(left_panel)

        right_panel = QFrame()
        right_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border-radius: 8px;
                border: 1px solid {Theme.BORDER};
            }}
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(10)

        perm_header_w = QWidget()
        perm_header_w.setStyleSheet("background: transparent;")
        perm_header_l = QHBoxLayout(perm_header_w)
        perm_header_l.setContentsMargins(0, 0, 0, 0)
        perm_header_l.setSpacing(8)

        self.perm_title = QLabel("Rol seçin →")
        self.perm_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.perm_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; background: transparent;")
        perm_header_l.addWidget(self.perm_title)
        perm_header_l.addStretch()

        self.select_all_btn = QPushButton("Tümünü Seç")
        self.select_all_btn.setCursor(Qt.PointingHandCursor)
        self.select_all_btn.setFixedHeight(28)
        self.select_all_btn.setVisible(False)
        self.select_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.INFO}; color: white;
                border: none; border-radius: 5px; padding: 0 12px;
                font-size: 11px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #5bc7e0; }}
        """)
        self.select_all_btn.clicked.connect(self._select_all_permissions)
        perm_header_l.addWidget(self.select_all_btn)

        self.clear_all_btn = QPushButton("Tümünü Kaldır")
        self.clear_all_btn.setCursor(Qt.PointingHandCursor)
        self.clear_all_btn.setFixedHeight(28)
        self.clear_all_btn.setVisible(False)
        self.clear_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_HOVER}; color: {Theme.TEXT_SECONDARY};
                border: none; border-radius: 5px; padding: 0 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{ background-color: {Theme.BORDER}; }}
        """)
        self.clear_all_btn.clicked.connect(self._clear_all_permissions)
        perm_header_l.addWidget(self.clear_all_btn)

        right_layout.addWidget(perm_header_w)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
        """)

        self.perm_grid_widget = QWidget()
        self.perm_grid_widget.setStyleSheet("background: transparent;")
        self.perm_grid_layout = QVBoxLayout(self.perm_grid_widget)
        self.perm_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.perm_grid_layout.setSpacing(8)

        placeholder = QLabel("← Soldaki listeden bir rol seçerek\nyetkilerini görüntüleyin ve düzenleyin.")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 14px; background: transparent; padding: 40px;")
        self.perm_grid_layout.addWidget(placeholder)

        scroll.setWidget(self.perm_grid_widget)
        right_layout.addWidget(scroll)

        self.save_perms_btn = QPushButton("💾 Yetkileri Kaydet")
        self.save_perms_btn.setCursor(Qt.PointingHandCursor)
        self.save_perms_btn.setFixedHeight(40)
        self.save_perms_btn.setVisible(False)
        self.save_perms_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.SUCCESS};
                color: {Theme.TEXT_DARK};
                border: none; border-radius: 8px;
                font-weight: bold; font-size: 13px;
            }}
            QPushButton:hover {{ background-color: #5fddb5; }}
        """)
        self.save_perms_btn.clicked.connect(self._on_save_permissions)
        right_layout.addWidget(self.save_perms_btn)

        layout.addWidget(right_panel)

        self._selected_role_id = None
        self._perm_checkboxes = {}
        self._refresh_roles()
        return widget


    def _refresh_roles(self):
        result = self.controller.get_all_roles()
        roles = result["data"] if result["success"] else []

        self.roles_table.setRowCount(len(roles))
        for i, role in enumerate(roles):
            perm_ids = json.loads(role.get("permission_IDs", "[]"))

            name_item = QTableWidgetItem(role["name"])
            name_item.setData(Qt.UserRole, role["ID"])
            if role["name"] == "admin":
                name_item.setForeground(QColor(Theme.WARNING))
            self.roles_table.setItem(i, 0, name_item)

            desc_item = QTableWidgetItem(role.get("description", ""))
            self.roles_table.setItem(i, 1, desc_item)

            count_item = QTableWidgetItem(str(len(perm_ids)))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.roles_table.setItem(i, 2, count_item)

            self.roles_table.setRowHeight(i, 40)

    def _on_role_selected(self):
        row = self.roles_table.currentRow()
        if row < 0:
            return

        item = self.roles_table.item(row, 0)
        if not item:
            return

        role_id = item.data(Qt.UserRole)
        self._selected_role_id = role_id
        role_name = item.text()

        if has_permission("role_manage"):
            self.edit_role_btn.setEnabled(True)
            self.delete_role_btn.setEnabled(role_name != "admin")

        self._load_permission_grid(role_id, role_name)

    def _load_permission_grid(self, role_id: int, role_name: str):
        self.perm_title.setText(f"🛡️ {role_name} — Yetkiler")

        while self.perm_grid_layout.count():
            child = self.perm_grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        result = self.controller.get_role(role_id)
        if not result["success"]:
            return

        role = result["data"]
        role_perm_ids = json.loads(role.get("permission_IDs", "[]"))

        all_perms = self.controller.permission_repo.get_all()
        perm_by_key = {p["key"]: p for p in all_perms}

        self._perm_checkboxes = {}

        is_admin_role = role_name == "admin"
        can_edit = has_permission("role_manage") and not is_admin_role

        if is_admin_role:
            note = QLabel("ℹ️ Admin rolü tüm yetkilere sahiptir ve düzenlenemez.")
            note.setStyleSheet(f"""
                color: {Theme.WARNING};
                background-color: transparent;
                font-size: 12px;
                font-style: italic;
                padding: 4px 0;
            """)
            self.perm_grid_layout.addWidget(note)

        for group_name, perm_keys in PERMISSION_GROUPS.items():
            group_frame = QFrame()
            group_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {Theme.BG_DARK};
                    border-radius: 8px;
                    border: 1px solid {Theme.BORDER};
                    padding: 4px;
                }}
            """)
            group_layout = QVBoxLayout(group_frame)
            group_layout.setContentsMargins(12, 8, 12, 8)
            group_layout.setSpacing(6)

            group_title = QLabel(f"📂 {group_name}")
            group_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
            group_title.setStyleSheet(f"color: {Theme.ACCENT}; background: transparent; border: none;")
            group_layout.addWidget(group_title)

            cb_widget = QWidget()
            cb_widget.setStyleSheet("background: transparent; border: none;")
            cb_layout = QGridLayout(cb_widget)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            cb_layout.setSpacing(6)

            col = 0
            row = 0
            max_cols = 3

            for key in perm_keys:
                perm = perm_by_key.get(key)
                if not perm:
                    continue

                label = PERMISSION_LABELS.get(key, perm.get("description", key))
                cb = QCheckBox(label)
                cb.setChecked(perm["ID"] in role_perm_ids)
                cb.setEnabled(can_edit)
                cb.setStyleSheet(f"""
                    QCheckBox {{
                        color: {Theme.TEXT_PRIMARY};
                        font-size: 12px;
                        spacing: 6px;
                        background: transparent;
                        border: none;
                        padding: 4px 8px;
                    }}
                    QCheckBox::indicator {{
                        width: 18px; height: 18px;
                        border-radius: 4px;
                        border: 2px solid {Theme.BORDER};
                        background-color: {Theme.BG_INPUT};
                    }}
                    QCheckBox::indicator:checked {{
                        background-color: {Theme.SUCCESS};
                        border-color: {Theme.SUCCESS};
                    }}
                    QCheckBox::indicator:disabled {{
                        background-color: {Theme.BG_HOVER};
                        border-color: {Theme.TEXT_MUTED};
                    }}
                    QCheckBox::indicator:checked:disabled {{
                        background-color: {Theme.SUCCESS};
                        border-color: {Theme.SUCCESS};
                    }}
                """)

                self._perm_checkboxes[perm["ID"]] = cb
                cb_layout.addWidget(cb, row, col)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

            group_layout.addWidget(cb_widget)
            self.perm_grid_layout.addWidget(group_frame)

        self.perm_grid_layout.addStretch()

        self.select_all_btn.setVisible(can_edit)
        self.clear_all_btn.setVisible(can_edit)
        self.save_perms_btn.setVisible(can_edit)

    def _select_all_permissions(self):
        for cb in self._perm_checkboxes.values():
            if cb.isEnabled():
                cb.setChecked(True)

    def _clear_all_permissions(self):
        for cb in self._perm_checkboxes.values():
            if cb.isEnabled():
                cb.setChecked(False)

    def _on_save_permissions(self):
        if self._selected_role_id is None:
            return

        selected_ids = [pid for pid, cb in self._perm_checkboxes.items() if cb.isChecked()]

        result = self.controller.update_role(self._selected_role_id, {
            "permission_IDs": selected_ids
        })

        if result["success"]:
            QMessageBox.information(self, "Başarılı",
                                    f"Yetkiler güncellendi ({len(selected_ids)} yetki atandı).")
            self._refresh_roles()
        else:
            QMessageBox.warning(self, "Hata", result["message"])

    def _on_add_role(self):
        dialog = RoleDialog(self)
        if dialog.exec_() == RoleDialog.Accepted:
            data = dialog.result_data
            result = self.controller.add_role(
                name=data["name"],
                description=data.get("description", ""),
                permission_ids=[]
            )
            if result["success"]:
                self._refresh_roles()
                QMessageBox.information(self, "Başarılı",
                                        f"'{data['name']}' rolü oluşturuldu. Şimdi yetkilerini atayabilirsiniz.")
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _on_edit_role(self):
        if self._selected_role_id is None:
            return

        result = self.controller.get_role(self._selected_role_id)
        if not result["success"]:
            QMessageBox.warning(self, "Hata", result["message"])
            return

        role = result["data"]
        if role["name"] == "admin":
            QMessageBox.warning(self, "Uyarı", "Admin rolü düzenlenemez.")
            return

        dialog = RoleDialog(self, edit_data=role)
        if dialog.exec_() == RoleDialog.Accepted:
            data = dialog.result_data
            update_data = {
                "name": data["name"],
                "description": data.get("description", ""),
            }
            result = self.controller.update_role(self._selected_role_id, update_data)
            if result["success"]:
                self._refresh_roles()
                self._load_permission_grid(self._selected_role_id, data["name"])
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _on_delete_role(self):
        if self._selected_role_id is None:
            return

        result = self.controller.get_role(self._selected_role_id)
        if not result["success"]:
            return
        role = result["data"]

        if role["name"] == "admin":
            QMessageBox.warning(self, "Uyarı", "Admin rolü silinemez.")
            return

        assigned = self.employee_role_repo.get_employees_by_role(self._selected_role_id)
        if assigned:
            QMessageBox.warning(self, "Uyarı",
                                f"Bu rol {len(assigned)} çalışana atanmış.\n"
                                "Önce çalışanlardan bu rolü kaldırmalısınız.")
            return

        reply = QMessageBox.question(
            self, "Rol Silme",
            f"'{role['name']}' rolünü silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        result = self.controller.delete_role(self._selected_role_id)
        if result["success"]:
            self._selected_role_id = None
            self._refresh_roles()
            self.perm_title.setText("Rol seçin →")
            while self.perm_grid_layout.count():
                child = self.perm_grid_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            placeholder = QLabel("← Soldaki listeden bir rol seçerek\nyetkilerini görüntüleyin ve düzenleyin.")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 14px; background: transparent; padding: 40px;")
            self.perm_grid_layout.addWidget(placeholder)
            self.select_all_btn.setVisible(False)
            self.clear_all_btn.setVisible(False)
            self.save_perms_btn.setVisible(False)
            if has_permission("role_manage"):
                self.edit_role_btn.setEnabled(False)
                self.delete_role_btn.setEnabled(False)
        else:
            QMessageBox.warning(self, "Hata", result["message"])


    def _build_permissions_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        info = QLabel("Sistemde tanımlı tüm yetkiler aşağıda listelenmiştir. "
                       "Yetkileri rollere atamak için 'Roller' sekmesini kullanın.")
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(info)

        filter_layout = QHBoxLayout()
        search_lbl = QLabel("🔍 Ara:")
        search_lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        self.perm_search = QLineEdit()
        self.perm_search.setPlaceholderText("Yetki adı veya açıklama ara...")
        self.perm_search.setStyleSheet(_input_style())
        self.perm_search.textChanged.connect(self._filter_permissions)
        filter_layout.addWidget(search_lbl)
        filter_layout.addWidget(self.perm_search)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        self.perms_table = QTableWidget()
        self.perms_table.setColumnCount(4)
        self.perms_table.setHorizontalHeaderLabels(["ID", "Yetki Anahtarı", "Açıklama", "Grup"])
        self.perms_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.perms_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.perms_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.perms_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.perms_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.perms_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.perms_table.verticalHeader().setVisible(False)
        self.perms_table.setStyleSheet(_table_style())
        layout.addWidget(self.perms_table)

        self._perm_page = 1
        self._perm_page_size = 100
        self._perm_filtered_data = []
        layout.addWidget(self._build_pagination_footer())

        self._refresh_permissions()
        return widget

    def _refresh_permissions(self):
        result = self.controller.get_all_permissions()
        self._all_permissions = result["data"] if result["success"] else []
        self._filter_permissions()

    def _filter_permissions(self):
        keyword = self.perm_search.text().strip().lower()
        data = self._all_permissions

        if keyword:
            data = [p for p in data if
                    keyword in p.get("key", "").lower() or
                    keyword in p.get("description", "").lower()]

        self._perm_filtered_data = data
        self._perm_page = 1
        self._render_permissions_page()

    def _get_permission_group(self, key: str) -> str:
        for group_name, keys in PERMISSION_GROUPS.items():
            if key in keys:
                return group_name
        return "—"

    def _render_permissions_page(self):
        data = self._perm_filtered_data
        total = len(data)
        total_pages = max(1, math.ceil(total / self._perm_page_size))
        if self._perm_page > total_pages:
            self._perm_page = total_pages

        start = (self._perm_page - 1) * self._perm_page_size
        end = start + self._perm_page_size
        page_data = data[start:end]

        self.perms_table.setRowCount(len(page_data))
        for i, p in enumerate(page_data):
            id_item = QTableWidgetItem(str(p["ID"]))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.perms_table.setItem(i, 0, id_item)

            key_item = QTableWidgetItem(p["key"])
            key_item.setForeground(QColor(Theme.INFO))
            self.perms_table.setItem(i, 1, key_item)

            self.perms_table.setItem(i, 2, QTableWidgetItem(p.get("description", "")))

            group = self._get_permission_group(p["key"])
            group_item = QTableWidgetItem(group)
            group_item.setTextAlignment(Qt.AlignCenter)
            group_item.setForeground(QColor(Theme.ACCENT))
            self.perms_table.setItem(i, 3, group_item)

            self.perms_table.setRowHeight(i, 36)

        self._update_pagination_footer(total, total_pages)


    def _build_pagination_footer(self) -> QFrame:
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

        self._pg_total_label = QLabel("Toplam: 0 kayıt")
        self._pg_total_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        layout.addWidget(self._pg_total_label)

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

        self._pg_btn_first = QPushButton("«")
        self._pg_btn_first.setCursor(Qt.PointingHandCursor)
        self._pg_btn_first.setStyleSheet(pagination_style)
        self._pg_btn_first.clicked.connect(lambda: self._pg_go(1))
        layout.addWidget(self._pg_btn_first)

        self._pg_btn_prev = QPushButton("‹ Önceki")
        self._pg_btn_prev.setCursor(Qt.PointingHandCursor)
        self._pg_btn_prev.setStyleSheet(pagination_style)
        self._pg_btn_prev.clicked.connect(lambda: self._pg_go(self._perm_page - 1))
        layout.addWidget(self._pg_btn_prev)

        self._pg_spin = QSpinBox()
        self._pg_spin.setRange(1, 1)
        self._pg_spin.setValue(1)
        self._pg_spin.setFixedWidth(60)
        self._pg_spin.setAlignment(Qt.AlignCenter)
        self._pg_spin.setStyleSheet(f"""
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
        self._pg_spin.valueChanged.connect(self._pg_go)
        layout.addWidget(self._pg_spin)

        self._pg_info = QLabel("/ 1")
        self._pg_info.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        layout.addWidget(self._pg_info)

        self._pg_btn_next = QPushButton("Sonraki ›")
        self._pg_btn_next.setCursor(Qt.PointingHandCursor)
        self._pg_btn_next.setStyleSheet(pagination_style)
        self._pg_btn_next.clicked.connect(lambda: self._pg_go(self._perm_page + 1))
        layout.addWidget(self._pg_btn_next)

        self._pg_btn_last = QPushButton("»")
        self._pg_btn_last.setCursor(Qt.PointingHandCursor)
        self._pg_btn_last.setStyleSheet(pagination_style)
        self._pg_btn_last.clicked.connect(lambda: self._pg_go(self._pg_spin.maximum()))
        layout.addWidget(self._pg_btn_last)

        return footer

    def _update_pagination_footer(self, total: int, total_pages: int):
        self._pg_spin.blockSignals(True)
        self._pg_spin.setRange(1, total_pages)
        self._pg_spin.setValue(self._perm_page)
        self._pg_spin.blockSignals(False)

        self._pg_info.setText(f"/ {total_pages}")
        self._pg_btn_first.setEnabled(self._perm_page > 1)
        self._pg_btn_prev.setEnabled(self._perm_page > 1)
        self._pg_btn_next.setEnabled(self._perm_page < total_pages)
        self._pg_btn_last.setEnabled(self._perm_page < total_pages)

        start = (self._perm_page - 1) * self._perm_page_size + 1
        end = min(self._perm_page * self._perm_page_size, total)
        if total == 0:
            self._pg_total_label.setText("Kayıt bulunamadı")
        else:
            self._pg_total_label.setText(f"Toplam {total} kayıttan {start}-{end} arası gösteriliyor")

    def _pg_go(self, page: int):
        total_pages = self._pg_spin.maximum()
        page = max(1, min(page, total_pages))
        if page != self._perm_page:
            self._perm_page = page
            self._render_permissions_page()


class RoleDialog(BaseDialog):
    def __init__(self, parent=None, edit_data: dict = None):
        self.edit_data = edit_data
        title = f"Rol Düzenle — {edit_data['name']}" if edit_data else "Yeni Rol Ekle"
        super().__init__(parent, title=title, width=420, height=280)

    def _setup_form(self):
        self.add_form_section_title("Rol Bilgileri")

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Rol adı girin (ör: Kasiyer, Depocu)")
        self.name_input.setStyleSheet(_input_style())
        self.add_form_field("Rol Adı", self.name_input, required=True)

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Rol açıklaması (opsiyonel)")
        self.desc_input.setStyleSheet(_input_style())
        self.add_form_field("Açıklama", self.desc_input)

        if self.edit_data:
            self.name_input.setText(self.edit_data.get("name", ""))
            self.desc_input.setText(self.edit_data.get("description", ""))

        self.form_layout.addStretch()

    def _on_save(self):
        name = self.name_input.text().strip()
        if not name:
            self.show_error("Rol adı boş bırakılamaz!")
            return

        self.result_data = {
            "name": name,
            "description": self.desc_input.text().strip(),
        }
        self.accept()

    def _input_style(self):
        return _input_style()
