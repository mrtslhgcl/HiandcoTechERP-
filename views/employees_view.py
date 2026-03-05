from PyQt5.QtWidgets import (QLineEdit, QComboBox, QMessageBox, QLabel,
                              QPushButton, QTextEdit, QMenu, QAction,
                              QHBoxLayout, QVBoxLayout, QWidget, QCheckBox,
                              QFileDialog, QFrame, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPixmap
from views.base_list_view import BaseListView
from views.base_dialog import BaseDialog
from controllers.employee_controller import EmployeeController
from controllers.auth_controller import AuthController
from database.employee_role_repository import EmployeeRoleRepository
from database.roles_repository import RoleRepository
from database.user_repository import UserRepository
from utils.theme import Theme
from utils.image_utils import save_entity_image, resolve_image_path
from datetime import datetime
import os


class EmployeesView(BaseListView):
    def __init__(self):
        self.controller = EmployeeController()
        self.auth_controller = AuthController()
        self.user_repo = UserRepository()
        self.employee_role_repo = EmployeeRoleRepository()
        self.role_repo = RoleRepository()

        columns = [
            {"key": "ID", "title": "ID", "width": 50, "align": "center"},
            {"key": "employee_code", "title": "Çalışan Kodu", "width": 110, "align": "center"},
            {"key": "first_name", "title": "Ad"},
            {"key": "last_name", "title": "Soyad"},
            {"key": "phone_number", "title": "Telefon", "width": 130, "align": "center"},
            {"key": "email", "title": "E-posta", "width": 180},
            {
                "key": "ID", "title": "Roller", "width": 160,
                "render": lambda val, item: self._get_role_names(val)
            },
            {
                "key": "ID", "title": "Hesap", "width": 90, "align": "center",
                "render": lambda val, item: self._get_user_status(val)
            },
            {
                "key": "status", "title": "Durum", "width": 80, "align": "center",
                "render": lambda val, item: "Aktif" if val == 1 else "Pasif"
            },
            {"key": "created_at", "title": "Kayıt Tarihi", "width": 130, "align": "center",
             "render": lambda val, item: val[:16] if val else "-"},
        ]

        super().__init__(
            title="Çalışan Yönetimi",
            columns=columns,
            add_permission="employee_create",
            edit_permission="employee_update",
            delete_permission="employee_delete"
        )

        self.add_btn.setText("+ Yeni Çalışan")
        self._setup_context_menu()
        self.refresh_data()


    def _get_role_names(self, employee_id) -> str:
        try:
            roles = self.employee_role_repo.get_roles_by_employee(employee_id)
            if not roles:
                return "—"
            names = []
            for er in roles:
                role = self.role_repo.get_by_id(er["role_ID"])
                if role:
                    names.append(role["name"])
            return ", ".join(names) if names else "—"
        except Exception:
            return "—"

    def _get_user_status(self, employee_id) -> str:
        try:
            user = self.user_repo.get_by_employee_id(employee_id)
            if user is None:
                return "Yok"
            return "Aktif" if user["is_active"] == 1 else "Pasif"
        except Exception:
            return "—"


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

        user = self.user_repo.get_by_employee_id(item["ID"])
        if user is None:
            create_user_action = QAction("🔑 Hesap Oluştur", self)
            create_user_action.triggered.connect(lambda: self._create_user_account(item))
            menu.addAction(create_user_action)
        else:
            reset_pw_action = QAction("🔒 Şifre Sıfırla", self)
            reset_pw_action.triggered.connect(lambda: self._reset_password(user))
            menu.addAction(reset_pw_action)

            if user["is_active"] == 1:
                deact_user_action = QAction("🚫 Hesabı Kapat", self)
                deact_user_action.triggered.connect(lambda: self._toggle_user_account(user, False))
            else:
                deact_user_action = QAction("✅ Hesabı Aç", self)
                deact_user_action.triggered.connect(lambda: self._toggle_user_account(user, True))
            menu.addAction(deact_user_action)

        menu.addSeparator()

        role_action = QAction("🎭 Rol Yönet", self)
        role_action.triggered.connect(lambda: self._manage_roles(item))
        menu.addAction(role_action)

        menu.addSeparator()

        is_active = item.get("status", 1)
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


    def _create_user_account(self, employee: dict):
        dialog = CreateUserDialog(self, employee=employee)
        if dialog.exec_() == CreateUserDialog.Accepted:
            data = dialog.result_data
            result = self.auth_controller.register_user(
                employee_id=employee["ID"],
                username=data["username"],
                password=data["password"]
            )
            if result["success"]:
                if data.get("role_id"):
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.employee_role_repo.assign_role(employee["ID"], data["role_id"], now)
                QMessageBox.information(self, "Başarılı", result["message"])
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _reset_password(self, user: dict):
        dialog = ResetPasswordDialog(self, username=user["username"])
        if dialog.exec_() == ResetPasswordDialog.Accepted:
            result = self.auth_controller.reset_password(user["ID"], dialog.result_data["password"])
            if result["success"]:
                QMessageBox.information(self, "Başarılı", result["message"])
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _toggle_user_account(self, user: dict, activate: bool):
        if activate:
            result = self.auth_controller.activate_user(user["ID"])
        else:
            result = self.auth_controller.deactivate_user(user["ID"])

        if result["success"]:
            self.refresh_data()
        else:
            QMessageBox.warning(self, "Hata", result["message"])


    def _manage_roles(self, employee: dict):
        dialog = ManageRolesDialog(self, employee=employee)
        if dialog.exec_() == ManageRolesDialog.Accepted:
            self.refresh_data()


    def _toggle_active(self, item: dict):
        is_active = item.get("status", 1)
        if is_active == 1:
            result = self.controller.deactivate_employee(item["ID"])
        else:
            result = self.controller.activate_employee(item["ID"])

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
                    str(item.get("employee_code", "")).lower(),
                    str(item.get("phone_number", "")).lower(),
                    str(item.get("email", "")).lower(),
                ]
                if any(text_lower in field for field in searchable):
                    self.filtered_data.append(item)

        self.current_page = 1
        self._update_pagination()
        self._render_table()


    def refresh_data(self):
        result = self.controller.get_all_employees()
        if result["success"]:
            self.set_data(result["data"])

    def _on_add(self):
        dialog = EmployeeDialog(self)
        if dialog.exec_() == EmployeeDialog.Accepted:
            data = dialog.result_data
            photo_source = data.pop("photo_path", "")
            data.pop("_photo_changed", None)

            result = self.controller.add_employee(**data)
            if result["success"]:
                employee_id = result.get("employee_id")
                if photo_source and employee_id:
                    rel_path, b64_data = save_entity_image(photo_source, "employees", employee_id)
                    update = {"photo_path": rel_path}
                    if b64_data:
                        update["image_data"] = b64_data
                    self.controller.employee_repo.update(employee_id, update)
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _on_edit(self, item: dict):
        dialog = EmployeeDialog(self, edit_data=item)
        if dialog.exec_() == EmployeeDialog.Accepted:
            data = dialog.result_data
            photo_source = data.pop("photo_path", "")
            photo_changed = data.pop("_photo_changed", False)

            if photo_changed:
                if photo_source:
                    rel_path, b64_data = save_entity_image(photo_source, "employees", item["ID"])
                    data["photo_path"] = rel_path
                    if b64_data:
                        data["image_data"] = b64_data
                else:
                    data["photo_path"] = ""
                    data["image_data"] = ""

            result = self.controller.update_employee(item["ID"], data)
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _on_delete(self, item: dict):
        name = f"{item.get('first_name', '')} {item.get('last_name', '')}"

        user = self.user_repo.get_by_employee_id(item["ID"])
        if user:
            QMessageBox.warning(self, "Hata",
                f"'{name}' çalışanının kullanıcı hesabı mevcut.\n"
                "Önce hesabı kapatın veya çalışanı pasife alın.")
            return

        if self.confirm_delete(name):
            result = self.controller.delete_employee(item["ID"])
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])


    def _render_table(self):
        super()._render_table()

        status_col = None
        account_col = None
        for i, col in enumerate(self.columns):
            if col["key"] == "status" and col["title"] == "Durum":
                status_col = i
            if col["title"] == "Hesap":
                account_col = i

        for row in range(self.table.rowCount()):
            if status_col is not None:
                cell = self.table.item(row, status_col)
                if cell:
                    if cell.text() == "Aktif":
                        cell.setForeground(QColor(Theme.SUCCESS))
                    else:
                        cell.setForeground(QColor(Theme.ERROR))

            if account_col is not None:
                cell = self.table.item(row, account_col)
                if cell:
                    if cell.text() == "Aktif":
                        cell.setForeground(QColor(Theme.SUCCESS))
                    elif cell.text() == "Pasif":
                        cell.setForeground(QColor(Theme.ERROR))
                    else:
                        cell.setForeground(QColor(Theme.TEXT_MUTED))


class EmployeeDialog(BaseDialog):
    def __init__(self, parent=None, edit_data: dict = None):
        self.edit_data = edit_data
        self._photo_changed = False

        if edit_data:
            stored_path = edit_data.get("photo_path", "")
            image_data = edit_data.get("image_data", "")
            self.selected_photo_path = resolve_image_path(stored_path, image_data) or ""
        else:
            self.selected_photo_path = ""

        title = "Çalışan Düzenle" if edit_data else "Yeni Çalışan Ekle"
        super().__init__(parent, title=title, width=520, height=580)

    def _setup_form(self):
        self.add_form_section_title("Fotoğraf")

        photo_widget = QWidget()
        photo_widget.setStyleSheet("background: transparent;")
        photo_layout = QHBoxLayout(photo_widget)
        photo_layout.setContentsMargins(0, 0, 0, 0)
        photo_layout.setSpacing(15)

        self.photo_preview = QLabel()
        self.photo_preview.setFixedSize(64, 64)
        self.photo_preview.setAlignment(Qt.AlignCenter)
        self.photo_preview.setStyleSheet(f"""
            QLabel {{
                background-color: {Theme.BG_INPUT};
                border: 2px dashed {Theme.BORDER};
                border-radius: 32px;
            }}
        """)
        self._update_photo_preview()
        photo_layout.addWidget(self.photo_preview)

        photo_btn_layout = QWidget()
        photo_btn_layout.setStyleSheet("background: transparent;")
        photo_btn_inner = QHBoxLayout(photo_btn_layout)
        photo_btn_inner.setContentsMargins(0, 0, 0, 0)
        photo_btn_inner.setSpacing(8)

        select_photo_btn = QPushButton("Fotoğraf Seç")
        select_photo_btn.setCursor(Qt.PointingHandCursor)
        select_photo_btn.setFixedHeight(34)
        select_photo_btn.setStyleSheet(f"""
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
        select_photo_btn.clicked.connect(self._select_photo)
        photo_btn_inner.addWidget(select_photo_btn)

        clear_photo_btn = QPushButton("Kaldır")
        clear_photo_btn.setCursor(Qt.PointingHandCursor)
        clear_photo_btn.setFixedHeight(34)
        clear_photo_btn.setStyleSheet(f"""
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
        clear_photo_btn.clicked.connect(self._clear_photo)
        photo_btn_inner.addWidget(clear_photo_btn)
        photo_btn_inner.addStretch()

        photo_layout.addWidget(photo_btn_layout)
        photo_layout.addStretch()
        self.form_layout.addWidget(photo_widget)

        self.add_form_separator()
        self.add_form_section_title("Kişisel Bilgiler")

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Örn: EMP001")
        self.code_input.setStyleSheet(self._input_style())
        self.add_form_field("Çalışan Kodu", self.code_input, required=True)

        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("Çalışan adını girin")
        self.first_name_input.setStyleSheet(self._input_style())
        self.add_form_field("Ad", self.first_name_input, required=True)

        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Çalışan soyadını girin")
        self.last_name_input.setStyleSheet(self._input_style())
        self.add_form_field("Soyad", self.last_name_input, required=True)

        self.add_form_separator()
        self.add_form_section_title("İletişim Bilgileri")

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("0555 123 4567")
        self.phone_input.setStyleSheet(self._input_style())
        self.add_form_field("Telefon", self.phone_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("ornek@firma.com")
        self.email_input.setStyleSheet(self._input_style())
        self.add_form_field("E-posta", self.email_input)

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Adres bilgisi (opsiyonel)")
        self.address_input.setStyleSheet(self._input_style())
        self.add_form_field("Adres", self.address_input)

        self.add_form_separator()
        self.add_form_section_title("Notlar")

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Çalışan hakkında notlar (opsiyonel)")
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
            self.code_input.setText(self.edit_data.get("employee_code", ""))
            self.first_name_input.setText(self.edit_data.get("first_name", ""))
            self.last_name_input.setText(self.edit_data.get("last_name", ""))
            self.phone_input.setText(self.edit_data.get("phone_number", ""))
            self.email_input.setText(self.edit_data.get("email", ""))
            self.address_input.setText(self.edit_data.get("address", ""))
            self.notes_input.setPlainText(self.edit_data.get("notes", ""))

        self.form_layout.addStretch()

    def _select_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Fotoğraf Seç", "",
            "Resim Dosyaları (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.selected_photo_path = file_path
            self._photo_changed = True
            self._update_photo_preview()

    def _clear_photo(self):
        self.selected_photo_path = ""
        self._photo_changed = True
        self._update_photo_preview()

    def _update_photo_preview(self):
        if self.selected_photo_path and os.path.exists(self.selected_photo_path):
            pixmap = QPixmap(self.selected_photo_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.photo_preview.setPixmap(scaled)
                return

        self.photo_preview.clear()
        self.photo_preview.setText("👤")
        self.photo_preview.setStyleSheet(f"""
            QLabel {{
                background-color: {Theme.BG_INPUT};
                border: 2px dashed {Theme.BORDER};
                border-radius: 32px;
                font-size: 28px;
            }}
        """)

    def _on_save(self):
        code = self.code_input.text().strip()
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()

        if not code:
            self.show_error("Çalışan kodu boş bırakılamaz!")
            return
        if not first_name:
            self.show_error("Çalışan adı boş bırakılamaz!")
            return
        if not last_name:
            self.show_error("Çalışan soyadı boş bırakılamaz!")
            return

        self.result_data = {
            "employee_code": code,
            "first_name": first_name,
            "last_name": last_name,
            "phone_number": self.phone_input.text().strip(),
            "email": self.email_input.text().strip(),
            "address": self.address_input.text().strip(),
            "notes": self.notes_input.toPlainText().strip(),
            "photo_path": self.selected_photo_path,
            "_photo_changed": self._photo_changed,
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


class CreateUserDialog(BaseDialog):
    def __init__(self, parent=None, employee: dict = None):
        self.employee = employee
        self.edit_data = None

        name = f"{employee['first_name']} {employee['last_name']}" if employee else ""
        super().__init__(parent, title=f"Hesap Oluştur — {name}", width=450, height=400)

    def _setup_form(self):
        self.add_form_section_title("Giriş Bilgileri")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Kullanıcı adını girin")
        self.username_input.setStyleSheet(self._input_style())
        self.add_form_field("Kullanıcı Adı", self.username_input, required=True)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Şifre girin")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(self._input_style())
        self.add_form_field("Şifre", self.password_input, required=True)

        self.password_confirm_input = QLineEdit()
        self.password_confirm_input.setPlaceholderText("Şifreyi tekrar girin")
        self.password_confirm_input.setEchoMode(QLineEdit.Password)
        self.password_confirm_input.setStyleSheet(self._input_style())
        self.add_form_field("Şifre Tekrar", self.password_confirm_input, required=True)

        self.add_form_separator()
        self.add_form_section_title("Rol Ataması")

        self.role_combo = QComboBox()
        self.role_combo.setStyleSheet(self._input_style())
        self.role_combo.addItem("-- Rol seçin (opsiyonel) --", None)

        roles = RoleRepository().get_all()
        for role in roles:
            self.role_combo.addItem(role["name"], role["ID"])

        self.add_form_field("Rol", self.role_combo)

        self.form_layout.addStretch()

    def _on_save(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        password_confirm = self.password_confirm_input.text()

        if not username:
            self.show_error("Kullanıcı adı boş bırakılamaz!")
            return
        if len(username) < 3:
            self.show_error("Kullanıcı adı en az 3 karakter olmalıdır!")
            return
        if not password:
            self.show_error("Şifre boş bırakılamaz!")
            return
        if len(password) < 4:
            self.show_error("Şifre en az 4 karakter olmalıdır!")
            return
        if password != password_confirm:
            self.show_error("Şifreler eşleşmiyor!")
            return

        self.result_data = {
            "username": username,
            "password": password,
            "role_id": self.role_combo.currentData(),
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


class ResetPasswordDialog(BaseDialog):
    def __init__(self, parent=None, username: str = ""):
        self.username = username
        self.edit_data = None

        super().__init__(parent, title=f"Şifre Sıfırla — {username}", width=420, height=300)

    def _setup_form(self):
        self.add_form_section_title("Yeni Şifre")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Yeni şifreyi girin")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(self._input_style())
        self.add_form_field("Yeni Şifre", self.password_input, required=True)

        self.password_confirm_input = QLineEdit()
        self.password_confirm_input.setPlaceholderText("Şifreyi tekrar girin")
        self.password_confirm_input.setEchoMode(QLineEdit.Password)
        self.password_confirm_input.setStyleSheet(self._input_style())
        self.add_form_field("Şifre Tekrar", self.password_confirm_input, required=True)

        self.form_layout.addStretch()

    def _on_save(self):
        password = self.password_input.text()
        password_confirm = self.password_confirm_input.text()

        if not password:
            self.show_error("Şifre boş bırakılamaz!")
            return
        if len(password) < 4:
            self.show_error("Şifre en az 4 karakter olmalıdır!")
            return
        if password != password_confirm:
            self.show_error("Şifreler eşleşmiyor!")
            return

        self.result_data = {"password": password}
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
            QLineEdit:focus {{
                border: 1px solid {Theme.BORDER_FOCUS};
            }}
        """


class ManageRolesDialog(BaseDialog):
    def __init__(self, parent=None, employee: dict = None):
        self.employee = employee
        self.edit_data = None
        self.employee_role_repo = EmployeeRoleRepository()
        self.role_repo = RoleRepository()
        self.role_checkboxes = []

        name = f"{employee['first_name']} {employee['last_name']}" if employee else ""
        super().__init__(parent, title=f"Rol Yönet — {name}", width=420, height=400)

    def _setup_form(self):
        self.add_form_section_title("Atanmış Roller")

        current_roles = self.employee_role_repo.get_roles_by_employee(self.employee["ID"])
        current_role_ids = {er["role_ID"] for er in current_roles}

        all_roles = self.role_repo.get_all()

        if not all_roles:
            info_label = QLabel("Henüz tanımlanmış rol bulunmuyor.")
            info_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 13px; background: transparent;")
            self.form_layout.addWidget(info_label)
        else:
            for role in all_roles:
                cb = QCheckBox(f"  {role['name']}")
                cb.setProperty("role_id", role["ID"])
                cb.setChecked(role["ID"] in current_role_ids)
                cb.setStyleSheet(f"""
                    QCheckBox {{
                        color: {Theme.TEXT_PRIMARY};
                        font-size: 13px;
                        spacing: 8px;
                        background: transparent;
                        padding: 6px 4px;
                    }}
                    QCheckBox::indicator {{
                        width: 18px;
                        height: 18px;
                        border-radius: 4px;
                        border: 2px solid {Theme.BORDER};
                        background-color: {Theme.BG_INPUT};
                    }}
                    QCheckBox::indicator:checked {{
                        background-color: {Theme.SUCCESS};
                        border-color: {Theme.SUCCESS};
                    }}
                    QCheckBox::indicator:hover {{
                        border-color: {Theme.ACCENT};
                    }}
                """)

                desc = role.get("description", "")
                if desc:
                    cb.setToolTip(desc)

                self.role_checkboxes.append(cb)
                self.form_layout.addWidget(cb)

        self.form_layout.addStretch()

    def _on_save(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        employee_id = self.employee["ID"]

        current_roles = self.employee_role_repo.get_roles_by_employee(employee_id)
        current_role_ids = {er["role_ID"] for er in current_roles}

        selected_role_ids = set()
        for cb in self.role_checkboxes:
            if cb.isChecked():
                selected_role_ids.add(cb.property("role_id"))

        to_remove = current_role_ids - selected_role_ids
        for role_id in to_remove:
            self.employee_role_repo.remove_role(employee_id, role_id)

        to_add = selected_role_ids - current_role_ids
        for role_id in to_add:
            self.employee_role_repo.assign_role(employee_id, role_id, now)

        self.accept()
