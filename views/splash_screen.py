from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont
import os


class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(500, 400)
        self._center_on_screen()
        self.steps = [
            ("Veritabanı kontrol ediliyor...", self._check_database),
            ("Tablolar oluşturuluyor...", self._check_tables),
            ("Veriler senkronize ediliyor...", self._sync_database),
            ("Admin kullanıcı kontrol ediliyor...", self._check_admin),
            ("Hazır!", self._finish),
        ]
        self.current_step = 0
        self.on_finished = None
        self._setup_ui()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
                border-radius: 16px;
                border: 2px solid #0f3460;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(40, 40, 40, 30)
        container_layout.setSpacing(15)

        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        logo_path = os.path.join(os.environ.get('HIANDCO_BASE_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled = pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled)
        else:
            self.logo_label.setText("LOGO")
            self.logo_label.setStyleSheet("color: #e94560; font-size: 36px; font-weight: bold;")
        container_layout.addWidget(self.logo_label)

        title = QLabel("Hiandco Tech ERP")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet("color: #ffffff; border: none; background: transparent;")
        container_layout.addWidget(title)

        version = QLabel("v1.0.0")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("color: #a6a6a6; font-size: 12px; border: none; background: transparent;")
        container_layout.addWidget(version)

        container_layout.addSpacing(20)

        self.progress = QProgressBar()
        self.progress.setFixedHeight(6)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #16213e;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #e94560;
                border-radius: 3px;
            }
        """)
        container_layout.addWidget(self.progress)

        self.status_label = QLabel("Başlatılıyor...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #a6a6a6; font-size: 12px; border: none; background: transparent;")
        container_layout.addWidget(self.status_label)

        layout.addWidget(container)

    def start(self):
        QTimer.singleShot(500, self._run_next_step)

    def _run_next_step(self):
        if self.current_step >= len(self.steps):
            return

        message, func = self.steps[self.current_step]
        self.status_label.setText(message)

        progress_value = int(((self.current_step + 1) / len(self.steps)) * 100)
        self.progress.setValue(progress_value)

        QApplication.processEvents()

        try:
            func()
        except Exception as e:
            self.status_label.setText(f"Hata: {str(e)}")
            self.status_label.setStyleSheet("color: #ff6b6b; font-size: 12px; border: none; background: transparent;")
            return

        self.current_step += 1

        if self.current_step < len(self.steps):
            QTimer.singleShot(600, self._run_next_step)

    def _check_database(self):
        from database.database_adapter import DatabaseAdapter
        db = DatabaseAdapter()
        db.fetch_all("SELECT 1")

    def _check_tables(self):
        from database.brand_repository import BrandRepository
        from database.category_repository import CategoryRepository
        from database.customer_repository import CustomerRepository
        from database.employee_repository import EmployeeRepository
        from database.employee_role_repository import EmployeeRoleRepository
        from database.location_repository import LocationRepository
        from database.order_repository import OrderRepository
        from database.order_item_repository import OrderItemRepository
        from database.payment_repository import PaymentRepository
        from database.permissions_repository import PermissionRepository
        from database.product_repository import ProductRepository
        from database.roles_repository import RoleRepository
        from database.stock_movement_repository import StockMovementRepository
        from database.supplier_repository import SupplierRepository
        from database.user_repository import UserRepository
        from database.variant_repository import VariantRepository
        from database.variant_type_repository import VariantTypeRepository

        BrandRepository()
        CategoryRepository()
        CustomerRepository()
        EmployeeRepository()
        EmployeeRoleRepository()
        LocationRepository()
        OrderRepository()
        OrderItemRepository()
        PaymentRepository()
        PermissionRepository()
        ProductRepository()
        RoleRepository()
        StockMovementRepository()
        SupplierRepository()
        UserRepository()
        VariantRepository()
        VariantTypeRepository()

    def _sync_database(self):
        from database.database_adapter import DatabaseAdapter
        db = DatabaseAdapter()
        if db.sync_enabled:
            self.status_label.setText("Veriler aktarılıyor...")
            QApplication.processEvents()
            db.migrate_local_to_turso()

            success = db.sync()
            if success:
                self.status_label.setText("✅ Turso ile senkronize edildi")
            else:
                self.status_label.setText("⚠️ Sync başarısız, lokal veri kullanılıyor")
                self.status_label.setStyleSheet(
                    "color: #ffd93d; font-size: 12px; border: none; background: transparent;"
                )
            QApplication.processEvents()
        elif db.mode == "hybrid":
            self.status_label.setText("⚠️ Turso bağlantısı kurulamadı")
            self.status_label.setStyleSheet(
                "color: #ffd93d; font-size: 12px; border: none; background: transparent;"
            )
            QApplication.processEvents()
        else:
            self.status_label.setText("Lokal veritabanı kullanılıyor")
            QApplication.processEvents()

    def _check_admin(self):
        from database.user_repository import UserRepository
        from database.employee_repository import EmployeeRepository
        from database.employee_role_repository import EmployeeRoleRepository
        from database.roles_repository import RoleRepository
        from database.permissions_repository import PermissionRepository
        import hashlib
        import json
        from datetime import datetime

        user_repo = UserRepository()
        employee_repo = EmployeeRepository()
        employee_role_repo = EmployeeRoleRepository()
        roles_repo = RoleRepository()
        perm_repo = PermissionRepository()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        all_permissions = [
            ("product_create", "Ürün ekleme"),
            ("product_read", "Ürün görüntüleme"),
            ("product_update", "Ürün güncelleme"),
            ("product_delete", "Ürün silme"),
            ("stock_manage", "Stok yönetimi"),
            ("stock_adjust", "Stok düzeltme"),
            ("order_create", "Sipariş oluşturma"),
            ("order_read", "Sipariş görüntüleme"),
            ("order_update", "Sipariş güncelleme"),
            ("order_cancel", "Sipariş iptal"),
            ("order_refund", "Sipariş iade"),
            ("payment_manage", "Ödeme yönetimi"),
            ("customer_create", "Müşteri ekleme"),
            ("customer_read", "Müşteri görüntüleme"),
            ("customer_update", "Müşteri güncelleme"),
            ("customer_delete", "Müşteri silme"),
            ("employee_create", "Çalışan ekleme"),
            ("employee_read", "Çalışan görüntüleme"),
            ("employee_update", "Çalışan güncelleme"),
            ("employee_delete", "Çalışan silme"),
            ("category_create", "Kategori ekleme"),
            ("category_read", "Kategori görüntüleme"),
            ("category_update", "Kategori güncelleme"),
            ("category_delete", "Kategori silme"),
            ("brand_create", "Marka ekleme"),
            ("brand_read", "Marka görüntüleme"),
            ("brand_update", "Marka güncelleme"),
            ("brand_delete", "Marka silme"),
            ("supplier_create", "Tedarikçi ekleme"),
            ("supplier_read", "Tedarikçi görüntüleme"),
            ("supplier_update", "Tedarikçi güncelleme"),
            ("supplier_delete", "Tedarikçi silme"),
            ("location_create", "Lokasyon ekleme"),
            ("location_read", "Lokasyon görüntüleme"),
            ("location_update", "Lokasyon güncelleme"),
            ("location_delete", "Lokasyon silme"),
            ("role_manage", "Rol yönetimi"),
            ("role_assign", "Rol atama"),
            ("permission_manage", "Yetki yönetimi"),
            ("user_manage", "Kullanıcı yönetimi"),
            ("user_reset_password", "Şifre sıfırlama"),
            ("log_read", "Log görüntüleme"),
            ("settings_manage", "Ayar yönetimi"),
        ]

        permission_ids = []
        for key, desc in all_permissions:
            existing = perm_repo.get_by_key(key)
            if not existing:
                pid = perm_repo.insert({
                    "key": key,
                    "description": desc,
                    "created_at": now
                })
                permission_ids.append(pid)
            else:
                permission_ids.append(existing["ID"])

        admin_role = roles_repo.get_by_name("admin")
        role_id = admin_role["ID"]

        admin_employees = employee_repo.get_by_field("email", "admin@system.local")
        if not admin_employees:
            employee_id = employee_repo.insert({
                "employee_code": "ADM001",
                "first_name": "System",
                "last_name": "Admin",
                "email": "admin@system.local",
                "phone_number": "",
                "address": "",
                "photo_path": "",
                "notes": "Sistem tarafından otomatik oluşturuldu",
                "status": 1,
                "created_at": now
            })
        else:
            employee_id = admin_employees[0]["ID"]

        existing_roles = employee_role_repo.get_roles_by_employee(employee_id)
        has_admin_role = any(er["role_ID"] == role_id for er in existing_roles)
        if not has_admin_role:
            employee_role_repo.assign_role(employee_id, role_id, now)

        admin_user = user_repo.get_by_username("admin")
        if not admin_user:
            hashed = hashlib.sha256("admin".encode()).hexdigest()
            user_repo.insert({
                "employee_ID": employee_id,
                "username": "admin",
                "password_hash": hashed,
                "is_active": 1,
                "created_at": now
            })

    def _finish(self):
        QTimer.singleShot(400, self._close_and_continue)

    def _close_and_continue(self):
        self.close()
        if self.on_finished:
            self.on_finished()