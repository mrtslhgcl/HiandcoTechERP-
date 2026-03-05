from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QStackedWidget, QApplication,
                              QMenu, QAction, QFrame, QLineEdit, QMessageBox,
                              QGraphicsDropShadowEffect, QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QFont, QPixmap, QColor, QCursor, QIcon
from utils.theme import Theme
from utils.session import Session
from utils.permission_helper import has_permission, is_admin
from views.base_dialog import BaseDialog
import os
import json

class MainWindow(QMainWindow):
    def __init__(self, user_data: dict):
        super().__init__()
        self.user_data = user_data
        self.session = Session()
        self.setWindowTitle("Hiandco Tech ERP")
        self.setMinimumSize(1200, 700)
        self.showMaximized()
        self.setStyleSheet(Theme.get_stylesheet())
        _base = os.environ.get('HIANDCO_BASE_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.setWindowIcon(QIcon(os.path.join(_base, "assets", "favicon.ico")))
        self.sidebar_buttons = {}
        self.active_page = None

        self._setup_ui()
        self._navigate("dashboard")

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

        right_side = QVBoxLayout()
        right_side.setContentsMargins(0, 0, 0, 0)
        right_side.setSpacing(0)

        topbar = self._create_topbar()
        right_side.addWidget(topbar)

        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet(f"background-color: {Theme.BG_DARK};")
        right_side.addWidget(self.content_stack)

        right_container = QWidget()
        right_container.setLayout(right_side)
        main_layout.addWidget(right_container)

    def _create_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setFixedWidth(Theme.SIDEBAR_WIDTH)
        sidebar.setStyleSheet(f"""
            QWidget {{
                background-color: {Theme.BG_SIDEBAR};
                border-right: 1px solid {Theme.BORDER};
            }}
        """)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 15, 12, 15)
        layout.setSpacing(4)

        logo_container = QWidget()
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(8, 5, 8, 15)

        logo_label = QLabel()
        logo_path = os.path.join(os.environ.get('HIANDCO_BASE_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled = pixmap.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled)
        logo_label.setStyleSheet("border: none;")
        logo_layout.addWidget(logo_label)

        app_name = QLabel("Hiandco Tech ERP")
        app_name.setFont(QFont("Segoe UI", 13, QFont.Bold))
        app_name.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; border: none;")
        logo_layout.addWidget(app_name)
        logo_layout.addStretch()

        layout.addWidget(logo_container)

        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {Theme.BORDER};")
        layout.addWidget(separator)
        layout.addSpacing(10)

        menu_items = [
            ("dashboard", "🏠", "Ana Sayfa", ""),
            ("products", "📦", "Ürünler", "product_create"),
            ("stock", "📊", "Stok", "stock_manage"),
            ("orders", "📋", "Siparişler", "order_create"),
            ("customers", "👥", "Müşteriler", "customer_create"),
            ("employees", "👔", "Çalışanlar", "employee_create"),
            ("categories", "📂", "Kategoriler", "category_create"),
            ("brands", "🏷️", "Markalar", "brand_create"),
            ("suppliers", "🚚", "Tedarikçiler", "supplier_create"),
            ("locations", "📍", "Lokasyonlar", "location_create"),
            ("variant_types", "🎨", "Varyant Tipleri", "variant_type_create"),
            ("roles", "🔐", "Roller & Yetkiler", "role_manage"),
        ]

        for key, icon, text, perm in menu_items:
            btn = QPushButton(f"  {icon}  {text}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(42)
            btn.setStyleSheet(Theme.get_sidebar_button_style(False))
            btn.clicked.connect(lambda checked, k=key: self._navigate(k))
            if perm and not has_permission(perm):
                btn.setVisible(False)
            layout.addWidget(btn)
            self.sidebar_buttons[key] = btn

        layout.addStretch()

        separator2 = QWidget()
        separator2.setFixedHeight(1)
        separator2.setStyleSheet(f"background-color: {Theme.BORDER};")
        layout.addWidget(separator2)
        layout.addSpacing(5)

        settings_btn = QPushButton("  ⚙️  Ayarlar")
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.setFixedHeight(42)
        settings_btn.setStyleSheet(Theme.get_sidebar_button_style(False))
        settings_btn.clicked.connect(lambda: self._navigate("settings"))
        if not is_admin():
            settings_btn.setVisible(False)
        layout.addWidget(settings_btn)
        self.sidebar_buttons["settings"] = settings_btn

        logout_btn = QPushButton("  🚪  Çıkış Yap")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setFixedHeight(42)
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.ERROR};
                border: none;
                border-radius: {Theme.BORDER_RADIUS_SMALL}px;
                padding: 12px 20px;
                text-align: left;
                font-size: {Theme.FONT_SIZE_NORMAL}px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 107, 107, 0.15);
            }}
        """)
        logout_btn.clicked.connect(self._handle_logout)
        layout.addWidget(logout_btn)

        return sidebar

    def _create_topbar(self) -> QWidget:
        topbar = QWidget()
        topbar.setFixedHeight(60)
        topbar.setStyleSheet(f"""
            QWidget {{
                background-color: {Theme.BG_DARK};
                border-bottom: 1px solid {Theme.BORDER};
            }}
        """)

        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(25, 0, 25, 0)

        self.page_title = QLabel("Ana Sayfa")
        self.page_title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.page_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; border: none;")
        layout.addWidget(self.page_title)

        layout.addStretch()

        self.notif_btn = QPushButton("🔔")
        self.notif_btn.setCursor(Qt.PointingHandCursor)
        self.notif_btn.setFixedSize(42, 42)
        self.notif_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 21px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_HOVER};
                border-color: {Theme.BORDER_FOCUS};
            }}
        """)
        self.notif_btn.clicked.connect(self._toggle_notifications)
        layout.addWidget(self.notif_btn)

        self.notif_badge = QLabel("0")
        self.notif_badge.setFixedSize(20, 20)
        self.notif_badge.setAlignment(Qt.AlignCenter)
        self.notif_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {Theme.ERROR};
                color: white;
                border-radius: 10px;
                font-size: 10px;
                font-weight: bold;
                border: none;
            }}
        """)
        self.notif_badge.setVisible(False)
        self.notif_badge.setParent(self.notif_btn)
        self.notif_badge.move(24, -2)

        layout.addSpacing(10)

        from database.database_adapter import DatabaseAdapter
        db = DatabaseAdapter()

        self.conn_status_btn = QPushButton()
        self.conn_status_btn.setCursor(Qt.PointingHandCursor)
        self.conn_status_btn.setFixedSize(36, 36)
        self.conn_status_btn.setToolTip("Veritabanı bağlantı durumu")
        self.conn_status_btn.clicked.connect(self._show_connection_info)
        layout.addWidget(self.conn_status_btn)
        self._update_connection_status()

        layout.addSpacing(6)

        session = Session()
        display_name = session.get_display_name()

        self.user_btn = QPushButton(f"  👤  {display_name}  ▾")
        self.user_btn.setCursor(Qt.PointingHandCursor)
        self.user_btn.setFixedHeight(42)
        self.user_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                padding: 0 16px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_HOVER};
                border-color: {Theme.BORDER_FOCUS};
            }}
        """)
        self.user_btn.clicked.connect(self._show_user_menu)
        layout.addWidget(self.user_btn)

        self._notif_panel = None
        self._notif_visible = False

        QTimer.singleShot(500, self._refresh_notifications)

        self._sync_timer = QTimer()
        self._sync_timer.timeout.connect(self._do_periodic_sync)
        sync_interval = db.sync_interval * 1000
        if db.sync_enabled and sync_interval > 0:
            self._sync_timer.start(sync_interval)

        return topbar


    def _update_connection_status(self):
        from database.database_adapter import DatabaseAdapter
        db = DatabaseAdapter()
        info = db.connection_info

        queue_size = info.get("queue_size", 0)

        if info["mode"] == "hybrid" and info["is_online"]:
            icon = "🟢"
            tip = "Turso Online — Senkronize"
            border_color = Theme.SUCCESS
        elif info["mode"] == "hybrid" and info.get("turso_available") and not info["is_online"]:
            icon = "🟠"
            tip = f"Turso Uyarı — {info.get('last_error', '?')}"
            border_color = Theme.WARNING
        elif info["mode"] == "hybrid" and not info.get("turso_available"):
            icon = "🔴"
            tip = f"Turso Çevrimdışı — Kuyrukta {queue_size} yazma bekliyor"
            border_color = Theme.ERROR
        else:
            icon = "💾"
            tip = "Lokal SQLite — Çevrimdışı Mod"
            border_color = Theme.TEXT_MUTED

        self.conn_status_btn.setText(icon)
        self.conn_status_btn.setToolTip(tip)
        self.conn_status_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {border_color};
                border-radius: 18px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_HOVER};
            }}
        """)

    def _do_periodic_sync(self):
        from database.database_adapter import DatabaseAdapter
        db = DatabaseAdapter()
        db.sync()
        self._update_connection_status()

    def _show_connection_info(self):
        from database.database_adapter import DatabaseAdapter
        db = DatabaseAdapter()
        info = db.connection_info

        if info["mode"] == "hybrid":
            queue_size = info.get("queue_size", 0)
            if info["is_online"]:
                status_text = "✅ Turso Online — Veriler senkronize"
            elif info.get("turso_available"):
                status_text = f"⚠️ Uyarı: {info.get('last_error', '?')}"
            else:
                status_text = f"🔴 Çevrimdışı — Kuyrukta {queue_size} yazma"

            msg = (
                f"Mod: Hybrid (Online + Lokal Yedek)\n"
                f"Durum: {status_text}\n"
                f"Sync Aralığı: {db.sync_interval} saniye\n"
                f"Kuyruk: {queue_size} bekleyen yazma\n\n"
                f"Verileriniz hem Turso sunucusunda hem de\n"
                f"lokal bilgisayarınızda yedeklenmektedir."
            )
        else:
            msg = (
                f"Mod: Lokal SQLite\n"
                f"Durum: 💾 Çevrimdışı çalışıyor\n\n"
                f"Online moda geçmek için db_config.json\n"
                f"dosyasında Turso bilgilerinizi yapılandırın."
            )

        QMessageBox.information(self, "Veritabanı Bağlantı Durumu", msg)


    def _show_user_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Theme.BG_CARD};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                padding: 6px 0;
                font-size: 13px;
            }}
            QMenu::item {{
                padding: 10px 24px;
            }}
            QMenu::item:selected {{
                background-color: {Theme.BG_HOVER};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {Theme.BORDER};
                margin: 4px 12px;
            }}
        """)

        session = Session()

        info_action = QAction(f"🏷️  {session.username}", self)
        info_action.setEnabled(False)
        menu.addAction(info_action)

        role_names = [r.get("name", "?") for r in session.roles]
        if role_names:
            role_action = QAction(f"🔐  {', '.join(role_names)}", self)
            role_action.setEnabled(False)
            menu.addAction(role_action)

        menu.addSeparator()

        change_pass = QAction("🔑  Şifre Değiştir", self)
        change_pass.triggered.connect(self._on_change_password)
        menu.addAction(change_pass)

        menu.addSeparator()

        logout_action = QAction("🚪  Çıkış Yap", self)
        logout_action.triggered.connect(self._handle_logout)
        menu.addAction(logout_action)

        btn_pos = self.user_btn.mapToGlobal(QPoint(0, self.user_btn.height()))
        menu.exec_(btn_pos)

    def _on_change_password(self):
        dialog = ChangePasswordDialog(self)
        dialog.exec_()


    def _toggle_notifications(self):
        if self._notif_panel and self._notif_visible:
            self._notif_panel.hide()
            self._notif_panel.deleteLater()
            self._notif_panel = None
            self._notif_visible = False
            return

        self._show_notification_panel()

    def _show_notification_panel(self):
        if self._notif_panel:
            self._notif_panel.hide()
            self._notif_panel.deleteLater()

        panel = NotificationPanel(self)
        panel.setParent(self)

        btn_pos = self.notif_btn.mapTo(self, QPoint(0, self.notif_btn.height() + 5))
        panel_x = btn_pos.x() - 320 + self.notif_btn.width()
        panel_y = btn_pos.y()

        if panel_x < 10:
            panel_x = 10

        panel.move(panel_x, panel_y)
        panel.show()
        panel.raise_()

        self._notif_panel = panel
        self._notif_visible = True

    def _refresh_notifications(self):
        try:
            notifications = self._collect_notifications()
            count = len(notifications)

            if count > 0:
                self.notif_badge.setText(str(count) if count <= 99 else "99+")
                self.notif_badge.setVisible(True)
                self.notif_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {Theme.WARNING};
                        border: 1px solid {Theme.WARNING};
                        border-radius: 21px;
                        font-size: 18px;
                    }}
                    QPushButton:hover {{
                        background-color: {Theme.BG_HOVER};
                    }}
                """)
            else:
                self.notif_badge.setVisible(False)
                self.notif_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {Theme.TEXT_PRIMARY};
                        border: 1px solid {Theme.BORDER};
                        border-radius: 21px;
                        font-size: 18px;
                    }}
                    QPushButton:hover {{
                        background-color: {Theme.BG_HOVER};
                        border-color: {Theme.BORDER_FOCUS};
                    }}
                """)
        except Exception:
            pass

    def _collect_notifications(self) -> list:
        from database.variant_repository import VariantRepository
        from database.product_repository import ProductRepository
        from database.order_repository import OrderRepository
        from database.order_item_repository import OrderItemRepository
        from database.payment_repository import PaymentRepository

        notifications = []

        try:
            variant_repo = VariantRepository()
            product_repo = ProductRepository()
            all_variants = variant_repo.get_all()

            for v in all_variants:
                quantities = json.loads(v.get("location_quantities", "{}"))
                total_qty = sum(int(q) for q in quantities.values()) if quantities else 0

                if total_qty == 0:
                    product = product_repo.get_by_id(v.get("product_ID"))
                    p_name = product.get("name", "?") if product else "?"
                    notifications.append({
                        "type": "zero_stock",
                        "icon": "🚫",
                        "title": f"{p_name} — {v.get('sku', '?')}",
                        "subtitle": "Stok tamamen tükendi!",
                        "color": Theme.ERROR,
                        "page": "stock",
                    })
                elif total_qty <= 10:
                    product = product_repo.get_by_id(v.get("product_ID"))
                    p_name = product.get("name", "?") if product else "?"
                    notifications.append({
                        "type": "low_stock",
                        "icon": "⚠️",
                        "title": f"{p_name} — {v.get('sku', '?')}",
                        "subtitle": f"Mevcut: {total_qty} / Min: 10",
                        "color": Theme.WARNING,
                        "page": "stock",
                    })
        except Exception:
            pass

        try:
            order_repo = OrderRepository()
            order_item_repo = OrderItemRepository()
            payment_repo = PaymentRepository()
            all_orders = order_repo.get_all()

            for o in all_orders:
                status = o.get("status", "")

                if status == "pending":
                    notifications.append({
                        "type": "pending_order",
                        "icon": "📋",
                        "title": f"Sipariş #{o['ID']}",
                        "subtitle": f"Beklemede — {o.get('created_at', '')[:10]}",
                        "color": Theme.INFO,
                        "page": "orders",
                    })

                if status in ("pending", "completed"):
                    order_total = order_item_repo.get_order_total(o["ID"])
                    paid_total = payment_repo.get_order_paid_total(o["ID"])
                    discount = float(o.get("discount_price", 0) or 0)
                    net_total = order_total - discount
                    remaining = net_total - paid_total
                    if remaining > 0.01:
                        notifications.append({
                            "type": "unpaid_order",
                            "icon": "💰",
                            "title": f"Sipariş #{o['ID']} — {remaining:,.2f} ₺",
                            "subtitle": "Ödenmemiş bakiye mevcut",
                            "color": Theme.WARNING,
                            "page": "orders",
                        })
        except Exception:
            pass

        return notifications

    def _navigate(self, page_key: str):
        for key, btn in self.sidebar_buttons.items():
            btn.setStyleSheet(Theme.get_sidebar_button_style(key == page_key))

        self.active_page = page_key

        if self._notif_panel and self._notif_visible:
            self._notif_panel.hide()
            self._notif_panel.deleteLater()
            self._notif_panel = None
            self._notif_visible = False

        titles = {
            "dashboard": "Ana Sayfa",
            "products": "Ürün Yönetimi",
            "stock": "Stok Yönetimi",
            "orders": "Sipariş Yönetimi",
            "customers": "Müşteri Yönetimi",
            "employees": "Çalışan Yönetimi",
            "categories": "Kategori Yönetimi",
            "brands": "Marka Yönetimi",
            "suppliers": "Tedarikçi Yönetimi",
            "locations": "Lokasyon Yönetimi",
            "variant_types": "Varyant Tipleri",
            "roles": "Roller & Yetkiler",
            "settings": "Ayarlar",
        }
        self.page_title.setText(titles.get(page_key, ""))

        page_widget = self._get_page_widget(page_key)

        self.content_stack.addWidget(page_widget)
        self.content_stack.setCurrentWidget(page_widget)

        QTimer.singleShot(300, self._refresh_notifications)

    def _get_page_widget(self, page_key: str) -> QWidget:
        if page_key == "dashboard":
            from views.dashboard_view import DashboardView
            return DashboardView()

        if page_key == "categories":
            from views.categories_view import CategoriesView
            return CategoriesView()

        if page_key == "brands":
            from views.brands_view import BrandsView
            return BrandsView()

        if page_key == "suppliers":
            from views.suppliers_view import SuppliersView
            return SuppliersView()
        
        if page_key == "locations":
            from views.locations_view import LocationsView
            return LocationsView()

        if page_key == "variant_types":
            from views.variant_types_view import VariantTypesView
            return VariantTypesView()
        
        if page_key == "products":
            from views.products_view import ProductsView
            return ProductsView()

        if page_key == "stock":
            from views.stock_view import StockView
            return StockView()

        if page_key == "customers":
            from views.customers_view import CustomersView
            return CustomersView()

        if page_key == "employees":
            from views.employees_view import EmployeesView
            return EmployeesView()

        if page_key == "orders":
            from views.orders_view import OrdersView
            return OrdersView()

        if page_key == "roles":
            from views.roles_permissions_view import RolesPermissionsView
            return RolesPermissionsView()
        
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        layout.setAlignment(Qt.AlignCenter)

        icon_map = {
            "products": "📦", "stock": "📊",
            "orders": "📋", "customers": "👥", "employees": "👔",
            "categories": "📂", "brands": "🏷️", "suppliers": "🚚",
            "locations": "📍", "roles": "🔐", "settings": "⚙️",
        }

        icon = QLabel(icon_map.get(page_key, "📄"))
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 64px;")
        layout.addWidget(icon)

        title_map = {
            "products": "Ürün Yönetimi",
            "stock": "Stok Yönetimi", "orders": "Sipariş Yönetimi",
            "customers": "Müşteri Yönetimi", "employees": "Çalışan Yönetimi",
            "categories": "Kategori Yönetimi", "brands": "Marka Yönetimi",
            "suppliers": "Tedarikçi Yönetimi", "locations": "Lokasyon Yönetimi",
            "roles": "Roller & Yetkiler", "settings": "Ayarlar",
        }

        title = QLabel(title_map.get(page_key, "Sayfa"))
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        layout.addWidget(title)

        subtitle = QLabel("Bu sayfa yakında eklenecek...")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 14px;")
        layout.addWidget(subtitle)

        return placeholder

    def _handle_logout(self):
        from controllers.auth_controller import AuthController
        auth = AuthController()
        auth.logout()
        self.close()

        from views.login_view import LoginView
        self._login = LoginView()
        self._login.on_login_success = self._on_relogin
        self._login.show()

    def _on_relogin(self, result: dict):
        self._login.close()
        new_window = MainWindow(result.get("user", {}))
        new_window.show()
        self._new_window = new_window


class ChangePasswordDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__(parent, title="🔑 Şifre Değiştir", width=420, height=360)

    def _setup_form(self):
        self.add_form_section_title("Şifre Bilgileri")

        input_style = f"""
            QLineEdit {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.BORDER_RADIUS_SMALL}px;
                padding: 8px 12px;
                font-size: {Theme.FONT_SIZE_NORMAL}px;
            }}
            QLineEdit:focus {{
                border-color: {Theme.BORDER_FOCUS};
            }}
        """

        self.old_pass = QLineEdit()
        self.old_pass.setPlaceholderText("Mevcut şifrenizi girin")
        self.old_pass.setEchoMode(QLineEdit.Password)
        self.old_pass.setStyleSheet(input_style)
        self.add_form_field("Mevcut Şifre", self.old_pass, required=True)

        self.new_pass = QLineEdit()
        self.new_pass.setPlaceholderText("Yeni şifrenizi girin (en az 4 karakter)")
        self.new_pass.setEchoMode(QLineEdit.Password)
        self.new_pass.setStyleSheet(input_style)
        self.add_form_field("Yeni Şifre", self.new_pass, required=True)

        self.confirm_pass = QLineEdit()
        self.confirm_pass.setPlaceholderText("Yeni şifrenizi tekrar girin")
        self.confirm_pass.setEchoMode(QLineEdit.Password)
        self.confirm_pass.setStyleSheet(input_style)
        self.add_form_field("Şifre Tekrar", self.confirm_pass, required=True)

        self.form_layout.addStretch()

    def _on_save(self):
        old_password = self.old_pass.text().strip()
        new_password = self.new_pass.text().strip()
        confirm = self.confirm_pass.text().strip()

        if not old_password:
            self.show_error("Mevcut şifrenizi girin!")
            return

        if not new_password:
            self.show_error("Yeni şifre boş bırakılamaz!")
            return

        if len(new_password) < 4:
            self.show_error("Yeni şifre en az 4 karakter olmalıdır!")
            return

        if new_password != confirm:
            self.show_error("Yeni şifreler eşleşmiyor!")
            return

        if old_password == new_password:
            self.show_error("Yeni şifre mevcut şifreden farklı olmalıdır!")
            return

        from controllers.auth_controller import AuthController
        auth = AuthController()
        session = Session()

        result = auth.change_password(session.user_id, old_password, new_password)

        if result["success"]:
            QMessageBox.information(self, "Başarılı", "Şifreniz başarıyla değiştirildi.")
            self.accept()
        else:
            self.show_error(result["message"])


class NotificationPanel(QFrame):
    def __init__(self, main_window: MainWindow):
        super().__init__(main_window)
        self.main_window = main_window
        self.setFixedSize(380, 460)
        self.setStyleSheet(f"""
            NotificationPanel {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.BORDER};
                border-radius: 12px;
            }}
        """)
        self.setObjectName("NotificationPanel")

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

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
        header_layout.setContentsMargins(16, 0, 16, 0)

        title = QLabel("🔔 Bildirimler")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; background: transparent;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        refresh_btn = QPushButton("🔄")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setFixedSize(30, 30)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_SECONDARY};
                border: none;
                font-size: 16px;
                border-radius: 15px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_HOVER};
            }}
        """)
        refresh_btn.clicked.connect(self._refresh)
        header_layout.addWidget(refresh_btn)

        close_btn = QPushButton("✕")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_SECONDARY};
                border: none;
                font-size: 14px;
                border-radius: 15px;
            }}
            QPushButton:hover {{
                background-color: {Theme.ERROR};
                color: white;
            }}
        """)
        close_btn.clicked.connect(self._close_panel)
        header_layout.addWidget(close_btn)

        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {Theme.BG_DARK};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {Theme.BORDER};
                border-radius: 4px;
                min-height: 30px;
            }}
        """)

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.content_layout.setSpacing(6)

        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)

        self._load_notifications()

    def _load_notifications(self):
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        notifications = self.main_window._collect_notifications()

        if not notifications:
            empty = QLabel("✅ Bildirim yok!\n\nHer şey yolunda görünüyor.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"""
                color: {Theme.SUCCESS};
                font-size: 14px;
                padding: 40px 20px;
                background: transparent;
            """)
            self.content_layout.addWidget(empty)
            self.content_layout.addStretch()
            return

        type_order = ["zero_stock", "low_stock", "unpaid_order", "pending_order"]
        type_labels = {
            "zero_stock": "🚫 Stokta Olmayan Ürünler",
            "low_stock": "⚠️ Düşük Stok Uyarıları",
            "unpaid_order": "💰 Ödenmemiş Siparişler",
            "pending_order": "📋 Bekleyen Siparişler",
        }

        grouped = {}
        for n in notifications:
            t = n["type"]
            if t not in grouped:
                grouped[t] = []
            grouped[t].append(n)

        for ntype in type_order:
            items = grouped.get(ntype, [])
            if not items:
                continue

            group_header = QLabel(f"{type_labels.get(ntype, ntype)}  ({len(items)})")
            group_header.setFont(QFont("Segoe UI", 11, QFont.Bold))
            group_header.setStyleSheet(f"""
                color: {Theme.TEXT_SECONDARY};
                background: transparent;
                padding: 6px 8px 2px 8px;
            """)
            self.content_layout.addWidget(group_header)

            for item in items[:5]:
                card = self._create_notification_card(item)
                self.content_layout.addWidget(card)

            if len(items) > 5:
                more = QLabel(f"   +{len(items) - 5} daha...")
                more.setStyleSheet(f"""
                    color: {Theme.TEXT_MUTED};
                    font-size: 11px;
                    font-style: italic;
                    padding: 2px 8px;
                    background: transparent;
                """)
                self.content_layout.addWidget(more)

        self.content_layout.addStretch()

    def _create_notification_card(self, notif: dict) -> QFrame:
        card = QFrame()
        card.setCursor(Qt.PointingHandCursor)
        card.setFixedHeight(56)
        accent = notif.get("color", Theme.TEXT_MUTED)
        page = notif.get("page", "")

        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_DARK};
                border-radius: 8px;
                border-left: 3px solid {accent};
            }}
            QFrame:hover {{
                background-color: {Theme.BG_HOVER};
            }}
        """)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(10, 6, 10, 6)
        card_layout.setSpacing(10)

        icon_lbl = QLabel(notif["icon"])
        icon_lbl.setFixedWidth(24)
        icon_lbl.setStyleSheet("font-size: 16px; background: transparent;")
        card_layout.addWidget(icon_lbl)

        text_w = QWidget()
        text_w.setStyleSheet("background: transparent;")
        text_l = QVBoxLayout(text_w)
        text_l.setContentsMargins(0, 0, 0, 0)
        text_l.setSpacing(2)

        title = QLabel(notif["title"])
        title.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY};
            font-size: 12px;
            font-weight: bold;
            background: transparent;
        """)
        title.setMaximumWidth(280)
        text_l.addWidget(title)

        subtitle = QLabel(notif["subtitle"])
        subtitle.setStyleSheet(f"""
            color: {Theme.TEXT_MUTED};
            font-size: 11px;
            background: transparent;
        """)
        text_l.addWidget(subtitle)

        card_layout.addWidget(text_w)
        card_layout.addStretch()

        if page:
            card.mousePressEvent = lambda e, p=page: self._go_to_page(p)

        return card

    def _go_to_page(self, page: str):
        self._close_panel()
        self.main_window._navigate(page)

    def _refresh(self):
        self._load_notifications()
        self.main_window._refresh_notifications()

    def _close_panel(self):
        self.main_window._notif_visible = False
        self.main_window._notif_panel = None
        self.hide()
        self.deleteLater()