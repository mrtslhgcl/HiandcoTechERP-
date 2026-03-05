from database.base_repository import BaseRepository


class VariantRepository(BaseRepository):
    def __init__(self):
        super().__init__("variants")
        self.create_table({
            "ID": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "product_ID": "INTEGER NOT NULL REFERENCES products(ID)",
            "sku": "TEXT NOT NULL UNIQUE",
            "barcode": "TEXT NOT NULL",
            "buy_price": "REAL DEFAULT 0.0",
            "sell_price": "REAL DEFAULT 0.0",
            "vat_included": "INTEGER DEFAULT 0",
            "vat_rate": "REAL DEFAULT 0.0",
            "location_quantities": "TEXT DEFAULT '{}'",
            "created_at": "TEXT NOT NULL"
        })

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS variant_attributes (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                variant_ID INTEGER NOT NULL REFERENCES variants(ID),
                variant_value_ID INTEGER NOT NULL REFERENCES variant_values(ID)
            )
        """)

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS product_images (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                product_ID INTEGER NOT NULL REFERENCES products(ID),
                variant_ID INTEGER DEFAULT NULL REFERENCES variants(ID),
                image_path TEXT NOT NULL,
                image_data TEXT DEFAULT ''
            )
        """)
        self._ensure_column("image_data", "TEXT DEFAULT ''", "product_images")

    def get_by_barcode(self, barcode: str) -> dict | None:
        results = self.get_by_field("barcode", barcode)
        return results[0] if results else None

    def get_by_sku(self, sku: str) -> dict | None:
        results = self.get_by_field("sku", sku)
        return results[0] if results else None

    def get_by_product(self, product_id: int) -> list[dict]:
        return self.get_by_field("product_ID", product_id)

    def search_by_barcode(self, keyword: str) -> list[dict]:
        return self.search("barcode", keyword)

    def search_by_sku(self, keyword: str) -> list[dict]:
        return self.search("sku", keyword)

    def get_low_stock_variants(self, threshold: int = 10) -> list[dict]:
        import json
        all_variants = self.get_all()
        low_stock = []
        for variant in all_variants:
            quantities = json.loads(variant.get("location_quantities", "{}"))
            total = sum(quantities.values())
            if total <= threshold:
                variant["_total_quantity"] = total
                low_stock.append(variant)
        return low_stock


    def add_attributes(self, variant_id: int, value_ids: list[int]):
        for value_id in value_ids:
            self.db.execute(
                "INSERT INTO variant_attributes (variant_ID, variant_value_ID) VALUES (?, ?)",
                (variant_id, value_id)
            )

    def delete_attributes(self, variant_id: int):
        self.db.execute(
            "DELETE FROM variant_attributes WHERE variant_ID = ?",
            (variant_id,)
        )

    def get_attributes(self, variant_id: int) -> list[dict]:
        query = """
            SELECT 
                vv.ID, vv.value, vv.variant_type_ID,
                vt.name as type_name
            FROM variant_attributes va
            JOIN variant_values vv ON va.variant_value_ID = vv.ID
            JOIN variant_types vt ON vv.variant_type_ID = vt.ID
            WHERE va.variant_ID = ?
        """
        return self.db.fetch_all(query, (variant_id,))

    def get_variant_with_attributes(self, variant_id: int) -> dict | None:
        variant = self.get_by_id(variant_id)
        if variant is None:
            return None
        variant["attributes"] = self.get_attributes(variant_id)
        return variant

    def get_by_product_with_attributes(self, product_id: int) -> list[dict]:
        variants = self.get_by_product(product_id)
        for variant in variants:
            variant["attributes"] = self.get_attributes(variant["ID"])
        return variants


    def add_image(self, product_id: int, image_path: str, variant_id: int = None, image_data: str = None) -> int:
        cursor = self.db.execute(
            "INSERT INTO product_images (product_ID, variant_ID, image_path, image_data) VALUES (?, ?, ?, ?)",
            (product_id, variant_id, image_path, image_data or "")
        )
        return cursor.lastrowid

    def get_images_by_product(self, product_id: int) -> list[dict]:
        return self.db.fetch_all(
            "SELECT * FROM product_images WHERE product_ID = ?",
            (product_id,)
        )

    def get_general_images(self, product_id: int) -> list[dict]:
        return self.db.fetch_all(
            "SELECT * FROM product_images WHERE product_ID = ? AND variant_ID IS NULL",
            (product_id,)
        )

    def get_images_by_variant(self, variant_id: int) -> list[dict]:
        return self.db.fetch_all(
            "SELECT * FROM product_images WHERE variant_ID = ?",
            (variant_id,)
        )

    def delete_image(self, image_id: int):
        self.db.execute(
            "DELETE FROM product_images WHERE ID = ?",
            (image_id,)
        )

    def delete_images_by_product(self, product_id: int):
        self.db.execute(
            "DELETE FROM product_images WHERE product_ID = ?",
            (product_id,)
        )

    def delete_images_by_variant(self, variant_id: int):
        self.db.execute(
            "DELETE FROM product_images WHERE variant_ID = ?",
            (variant_id,)
        )

    def get_image_by_id(self, image_id: int) -> dict | None:
        results = self.db.fetch_all(
            "SELECT * FROM product_images WHERE ID = ?",
            (image_id,)
        )
        return results[0] if results else None