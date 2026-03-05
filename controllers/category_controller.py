from datetime import datetime
from database.category_repository import CategoryRepository
from database.product_repository import ProductRepository
from utils.logger import Logger
from utils.session import Session


class CategoryController:
    def __init__(self):
        self.category_repo = CategoryRepository()
        self.product_repo = ProductRepository()
        self.logger = Logger()
        self.session = Session()

    def _get_user(self) -> str:
        return self.session.get_log_user()

    def add_category(self, name: str, description: str = "",
                     parent_id: int = None) -> dict:

        if not self.session.has_permission("category_create"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok", "category_id": None}

        existing = self.category_repo.get_by_name(name)
        if existing:
            return {"success": False, "message": "Bu kategori adı zaten mevcut", "category_id": None}

        if parent_id is not None:
            parent = self.category_repo.get_by_id(parent_id)
            if parent is None:
                return {"success": False, "message": "Üst kategori bulunamadı", "category_id": None}

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        category_id = self.category_repo.insert({
            "name": name,
            "description": description,
            "parent_category_ID": parent_id,
            "created_at": now
        })

        self.logger.info(self._get_user(), "CategoryController", "Kategori eklendi", {
            "category_id": category_id,
            "name": name,
            "parent_id": parent_id
        })

        return {"success": True, "message": "Kategori başarıyla eklendi", "category_id": category_id}

    def update_category(self, category_id: int, data: dict) -> dict:
        if not self.session.has_permission("category_update"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        category = self.category_repo.get_by_id(category_id)
        if category is None:
            return {"success": False, "message": "Kategori bulunamadı"}

        if "name" in data and data["name"] != category["name"]:
            existing = self.category_repo.get_by_name(data["name"])
            if existing:
                return {"success": False, "message": "Bu kategori adı zaten mevcut"}

        if "parent_category_ID" in data and data["parent_category_ID"] is not None:
            if data["parent_category_ID"] == category_id:
                return {"success": False, "message": "Kategori kendisinin üst kategorisi olamaz"}
            parent = self.category_repo.get_by_id(data["parent_category_ID"])
            if parent is None:
                return {"success": False, "message": "Üst kategori bulunamadı"}
            if self._is_descendant(data["parent_category_ID"], category_id):
                return {"success": False, "message": "Döngüsel kategori ilişkisi oluşturulamaz"}

        self.category_repo.update(category_id, data)

        self.logger.info(self._get_user(), "CategoryController", "Kategori güncellendi", {
            "category_id": category_id,
            "updated_fields": list(data.keys())
        })

        return {"success": True, "message": "Kategori başarıyla güncellendi"}

    def delete_category(self, category_id: int) -> dict:
        if not self.session.has_permission("category_delete"):
            return {"success": False, "message": "Bu işlem için yetkiniz yok"}

        category = self.category_repo.get_by_id(category_id)
        if category is None:
            return {"success": False, "message": "Kategori bulunamadı"}

        children = self.category_repo.get_children(category_id)
        if children:
            return {"success": False, "message": f"Bu kategorinin {len(children)} alt kategorisi var. Önce alt kategorileri silin."}

        products = self.product_repo.get_by_any_category(category_id)
        if products:
            return {"success": False, "message": f"Bu kategoride {len(products)} ürün var. Önce ürünlerin kategorisini değiştirin."}

        self.category_repo.delete(category_id)

        self.logger.info(self._get_user(), "CategoryController", "Kategori silindi", {
            "category_id": category_id,
            "name": category["name"]
        })

        return {"success": True, "message": "Kategori başarıyla silindi"}

    def get_category(self, category_id: int) -> dict:
        category = self.category_repo.get_by_id(category_id)
        if category is None:
            return {"success": False, "message": "Kategori bulunamadı", "data": None}

        if category.get("parent_category_ID"):
            parent = self.category_repo.get_by_id(category["parent_category_ID"])
            category["parent_name"] = parent["name"] if parent else "Bilinmiyor"
        else:
            category["parent_name"] = None

        category["children"] = self.category_repo.get_children(category_id)

        return {"success": True, "message": "", "data": category}

    def get_all_categories(self) -> dict:

        categories = self.category_repo.get_all()
        return {"success": True, "message": "", "data": categories}

    def get_root_categories(self) -> dict:
        categories = self.category_repo.get_root_categories()
        return {"success": True, "message": "", "data": categories}

    def get_children(self, category_id: int) -> dict:
        category = self.category_repo.get_by_id(category_id)
        if category is None:
            return {"success": False, "message": "Kategori bulunamadı", "data": None}

        children = self.category_repo.get_children(category_id)
        return {"success": True, "message": "", "data": children}

    def get_category_tree(self) -> dict:
        all_categories = self.category_repo.get_all()
        tree = self._build_tree(all_categories, None)
        return {"success": True, "message": "", "data": tree}

    def search_categories(self, keyword: str) -> dict:
        categories = self.category_repo.search_by_name(keyword)
        return {"success": True, "message": "", "data": categories}

    def _build_tree(self, categories: list[dict], parent_id: int | None) -> list[dict]:
        tree = []
        for cat in categories:
            if cat.get("parent_category_ID") == parent_id:
                node = dict(cat)
                node["children"] = self._build_tree(categories, cat["ID"])
                tree.append(node)
        return tree

    def _is_descendant(self, category_id: int, target_id: int) -> bool:
        children = self.category_repo.get_children(target_id)
        for child in children:
            if child["ID"] == category_id:
                return True
            if self._is_descendant(category_id, child["ID"]):
                return True
        return False
    
    def get_category_by_name(self, name: str) -> dict:
        category = self.category_repo.get_by_name(name)
        if category is None:
            return {"success": False, "message": "Kategori bulunamadı", "data": None}
        return {"success": True, "message": "", "data": category}
    
