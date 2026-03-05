from database.base_repository import BaseRepository
from datetime import datetime


class PermissionRepository(BaseRepository):
    def __init__(self):
        super().__init__("permissions")
        self.create_table({
            "ID": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "key": "TEXT NOT NULL UNIQUE",
            "description": "TEXT DEFAULT ''",
            "created_at": "TEXT NOT NULL"
        })
        self._seed_permissions()

    def _seed_permissions(self):
        default_permissions = [
            ("category_create", "Kategori ekleme"),
            ("category_update", "Kategori güncelleme"),
            ("category_delete", "Kategori silme"),
            ("brand_create", "Marka ekleme"),
            ("brand_update", "Marka güncelleme"),
            ("brand_delete", "Marka silme"),
            ("supplier_create", "Tedarikçi ekleme"),
            ("supplier_update", "Tedarikçi güncelleme"),
            ("supplier_delete", "Tedarikçi silme"),
            ("location_create", "Lokasyon ekleme"),
            ("location_update", "Lokasyon güncelleme"),
            ("location_delete", "Lokasyon silme"),
            ("variant_type_create", "Varyant tipi ekleme"),
            ("variant_type_update", "Varyant tipi güncelleme"),
            ("variant_type_delete", "Varyant tipi silme"),
            ("product_create", "Ürün ekleme"),
            ("product_update", "Ürün güncelleme"),
            ("product_delete", "Ürün silme"),
            ("stock_create", "Stok ekleme"),
            ("stock_update", "Stok güncelleme"),
            ("stock_delete", "Stok silme"),
            ("customer_create", "Müşteri ekleme"),
            ("customer_update", "Müşteri güncelleme"),
            ("customer_delete", "Müşteri silme"),
            ("order_create", "Sipariş ekleme"),
            ("order_update", "Sipariş güncelleme"),
            ("order_delete", "Sipariş silme"),
            ("order_cancel", "Sipariş iptali"),
            ("order_refund", "Sipariş iadesi"),
            ("payment_manage", "Ödeme yönetimi"),
            ("employee_create", "Çalışan ekleme"),
            ("employee_update", "Çalışan güncelleme"),
            ("employee_delete", "Çalışan silme"),
            ("user_manage", "Kullanıcı hesap yönetimi"),
            ("user_reset_password", "Kullanıcı şifre sıfırlama"),
            ("role_manage", "Rol yönetimi"),
            ("role_assign", "Rol atama"),
            ("permission_manage", "Yetki yönetimi"),
            ("all", "Tüm yetkiler"),
        ]

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for key, description in default_permissions:
            existing = self.get_by_key(key)
            if existing is None:
                self.insert({
                    "key": key,
                    "description": description,
                    "created_at": now
                })

    def get_by_key(self, key: str) -> dict | None:
        results = self.get_by_field("key", key)
        return results[0] if results else None

    def search_by_key(self, keyword: str) -> list[dict]:
        return self.search("key", keyword)

    def get_all_permissions(self) -> list[dict]:
        return self.get_all()