from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFrame, 
    QDialog, QFormLayout, QComboBox, QTreeWidget, QTreeWidgetItem, 
    QFileDialog, QTabWidget, QScrollArea, QGridLayout, QSizePolicy,
    QSpinBox, QDoubleSpinBox, QCheckBox, QMenu
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
import os
import tempfile
from utils.image_utils import save_entity_image, resolve_image_path
from controllers.product_controller import ProductController
from controllers.category_controller import CategoryController
from controllers.brand_controller import BrandController
from controllers.supplier_controller import SupplierController
from controllers.variant_type_controller import VariantTypeController
from controllers.stock_controller import StockController
from views.base_dialog import BaseDialog
from utils.theme import Theme

from views.base_list_view import BaseListView


class ProductsView(BaseListView):
    def __init__(self):
        self.product_controller = ProductController()
        self.category_controller = CategoryController()
        self.brand_controller = BrandController()
        self.supplier_controller = SupplierController()
        self.stock_controller = StockController()

        columns = [
            {"key": "ID",               "title": "ID",                 "width": 60,  "align": "center"},
            {"key": "name",             "title": "Ad"},
            {"key": "main_category_ID", "title": "Kategori",           "width": 120, "render": self.render_category},
            {"key": "brand_ID",         "title": "Marka",              "width": 120, "render": self.render_brand},
            {"key": "supplier_ID",      "title": "Tedarikçi",          "width": 120, "render": self.render_supplier},
            {"key": "sale_unit",        "title": "Satış Birimi",       "width": 100, "align": "center"},
            {"key": "ID",               "title": "Toplam Stok",        "width": 100, "render": self.render_stock, "align": "center"},
            {"key": "is_active",        "title": "Durum",              "width": 80,  "render": lambda v, _: "Aktif" if v else "Pasif", "align": "center"},
            {"key": "created_at",       "title": "Oluşturulma Tarihi", "width": 150, "align": "center"},
        ]

        super().__init__(
            title="Ürünler",
            columns=columns,
            add_permission="product_create",
            edit_permission="product_update",
            delete_permission="product_delete"
        )

        self.table.setSelectionMode(QTableWidget.ExtendedSelection)

        self.bulk_barcode_btn = QPushButton("🔲 Toplu Barkod")
        self.bulk_barcode_btn.setCursor(Qt.PointingHandCursor)
        self.bulk_barcode_btn.setFixedHeight(36)
        self.bulk_barcode_btn.setStyleSheet(Theme.get_outline_button_style())
        self.bulk_barcode_btn.clicked.connect(self._on_bulk_barcode)
        self.filter_layout.addWidget(self.bulk_barcode_btn)

        self._setup_context_menu()
        self.refresh_data()

    def refresh_data(self):
        result = self.product_controller.get_all_products()
        if result["success"]:
            self.set_data(result["data"])

    def _setup_context_menu(self):
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return

        item = self.table.item(row, 0)
        if not item:
            return
        product_id = item.data(Qt.UserRole)

        product = None
        for p in self.data:
            if p.get("ID") == product_id:
                product = p
                break
        if not product:
            return

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Theme.BG_SIDEBAR};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 5px;
            }}
            QMenu::item {{
                padding: 8px 25px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {Theme.BG_HOVER};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {Theme.BORDER};
                margin: 4px 10px;
            }}
        """)

        header = menu.addAction(f"📦 {product.get('name', '')}")
        header.setEnabled(False)
        menu.addSeparator()

        barcode_action = menu.addAction("🔲 Barkod Oluştur")

        copy_action = menu.addAction("📋 Ürünü Kopyala")

        menu.addSeparator()

        is_active = product.get("is_active", 1)
        if is_active:
            toggle_action = menu.addAction("⛔ Pasife Al")
        else:
            toggle_action = menu.addAction("✅ Aktife Al")

        menu.addSeparator()

        edit_action = menu.addAction("✏️ Düzenle")
        delete_action = menu.addAction("🗑️ Sil")

        action = menu.exec_(self.table.viewport().mapToGlobal(pos))

        if action == barcode_action:
            self._generate_barcode(product)
        elif action == copy_action:
            self._copy_product(product)
        elif action == toggle_action:
            self._toggle_active(product)
        elif action == edit_action:
            self._on_edit(product)
        elif action == delete_action:
            self._on_delete(product)

    def _generate_barcode(self, product: dict):
        variants_result = self.product_controller.get_product_variants(product["ID"])
        if not variants_result["success"] or not variants_result["data"]:
            QMessageBox.warning(self, "Uyarı", "Bu ürüne ait varyant bulunamadı.")
            return

        variants = variants_result["data"]

        if len(variants) > 1:
            from PyQt5.QtWidgets import QInputDialog
            items = [f"{v['sku']} ({v['barcode']})" for v in variants]
            selected, ok = QInputDialog.getItem(
                self, "Varyant Seç", "Barkod oluşturulacak varyantı seçin:",
                items, 0, False
            )
            if not ok:
                return
            idx = items.index(selected)
            variant = variants[idx]
        else:
            variant = variants[0]

        barcode_value = variant.get("barcode", "")
        if not barcode_value:
            QMessageBox.warning(self, "Uyarı", "Bu varyantın barkod değeri boş.")
            return

        try:
            import barcode
            from barcode.writer import ImageWriter

            barcode_str = str(barcode_value).strip()
            if len(barcode_str) == 13 and barcode_str.isdigit():
                code = barcode.get('ean13', barcode_str, writer=ImageWriter())
            elif len(barcode_str) == 8 and barcode_str.isdigit():
                code = barcode.get('ean8', barcode_str, writer=ImageWriter())
            else:
                code = barcode.get('code128', barcode_str, writer=ImageWriter())

            temp_dir = tempfile.gettempdir()
            filename = code.save(os.path.join(temp_dir, f"barcode_{barcode_str}"))

            self._show_barcode_preview(filename, product["name"], variant["sku"], barcode_str)

        except ImportError:
            QMessageBox.warning(
                self, "Eksik Kütüphane",
                "Barkod oluşturmak için 'python-barcode' ve 'Pillow' kütüphaneleri gerekli.\n\n"
                "Kurulum: pip install python-barcode Pillow"
            )
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Barkod oluşturma hatası:\n{str(e)}")

    def _show_barcode_preview(self, image_path: str, product_name: str, sku: str, barcode_value: str):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Barkod: {sku}")
        dialog.setFixedSize(500, 380)
        dialog.setStyleSheet(f"background-color: {Theme.BG_DARK}; color: {Theme.TEXT_PRIMARY};")

        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        info = QLabel(f"📦 {product_name}\nSKU: {sku} | Barkod: {barcode_value}")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 14px; font-weight: bold;")
        layout.addWidget(info)

        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaledToWidth(400, Qt.SmoothTransformation)
            img_label = QLabel()
            img_label.setPixmap(pixmap)
            img_label.setAlignment(Qt.AlignCenter)
            img_label.setStyleSheet(f"background-color: white; border-radius: 8px; padding: 15px;")
            layout.addWidget(img_label)

        btn_layout = QHBoxLayout()

        save_btn = QPushButton("💾 Kaydet")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setFixedHeight(38)
        save_btn.setStyleSheet(Theme.get_button_style("success"))
        save_btn.clicked.connect(lambda: self._save_barcode(image_path, barcode_value, dialog))
        btn_layout.addWidget(save_btn)

        close_btn = QPushButton("✖ Kapat")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedHeight(38)
        close_btn.setStyleSheet(Theme.get_button_style("secondary"))
        close_btn.clicked.connect(dialog.close)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
        dialog.exec_()

    def _save_barcode(self, source_path: str, barcode_value: str, dialog: QDialog):
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Barkodu Kaydet",
            f"barkod_{barcode_value}.png",
            "PNG Dosyası (*.png);;Tüm Dosyalar (*)"
        )
        if save_path:
            import shutil
            shutil.copy2(source_path, save_path)
            QMessageBox.information(self, "Başarılı", f"Barkod kaydedildi:\n{save_path}")
            dialog.close()

    def _copy_product(self, product: dict):
        new_name = f"{product['name']} (Kopya)"
        result = self.product_controller.add_product(
            name=new_name,
            description=product.get("description", ""),
            main_category_id=product.get("main_category_ID"),
            extra_category_ids=[],
            brand_id=product.get("brand_ID"),
            supplier_id=product.get("supplier_ID"),
            sale_unit=product.get("sale_unit", "Adet")
        )
        if result["success"]:
            QMessageBox.information(self, "Başarılı",
                f"Ürün kopyalandı: '{new_name}'\n\nVaryantları düzenleme ekranından ekleyebilirsiniz.")
            self.refresh_data()
        else:
            QMessageBox.warning(self, "Hata", result["message"])

    def _toggle_active(self, product: dict):
        is_active = product.get("is_active", 1)
        if is_active:
            result = self.product_controller.deactivate_product(product["ID"])
            action = "pasife alındı"
        else:
            result = self.product_controller.activate_product(product["ID"])
            action = "aktife alındı"

        if result["success"]:
            QMessageBox.information(self, "Başarılı", f"'{product['name']}' {action}.")
            self.refresh_data()
        else:
            QMessageBox.warning(self, "Hata", result["message"])

    def _on_bulk_barcode(self):
        selected_rows = set()
        for idx in self.table.selectedIndexes():
            selected_rows.add(idx.row())

        if not selected_rows:
            QMessageBox.warning(self, "Uyarı",
                "Lütfen tablodan bir veya birden fazla ürün seçin.\n\n"
                "İpucu: Ctrl tuşuna basılı tutarak çoklu seçim yapabilirsiniz.")
            return

        product_ids = set()
        for row in selected_rows:
            item = self.table.item(row, 0)
            if item:
                product_ids.add(item.data(Qt.UserRole))

        barcode_list = []
        for pid in product_ids:
            product = None
            for p in self.data:
                if p.get("ID") == pid:
                    product = p
                    break
            if not product:
                continue

            variants_result = self.product_controller.get_product_variants(pid)
            if variants_result["success"]:
                for v in variants_result["data"]:
                    bc = v.get("barcode", "")
                    if bc:
                        barcode_list.append({
                            "product_name": product["name"],
                            "sku": v["sku"],
                            "barcode": bc
                        })

        if not barcode_list:
            QMessageBox.warning(self, "Uyarı", "Seçili ürünlerin varyantlarında barkod bulunamadı.")
            return

        try:
            import barcode
            from barcode.writer import ImageWriter
            from PIL import Image

            temp_dir = tempfile.gettempdir()
            image_paths = []

            for item in barcode_list:
                barcode_str = str(item["barcode"]).strip()
                if len(barcode_str) == 13 and barcode_str.isdigit():
                    code = barcode.get('ean13', barcode_str, writer=ImageWriter())
                elif len(barcode_str) == 8 and barcode_str.isdigit():
                    code = barcode.get('ean8', barcode_str, writer=ImageWriter())
                else:
                    code = barcode.get('code128', barcode_str, writer=ImageWriter())

                filename = code.save(os.path.join(temp_dir, f"bulk_{barcode_str}"))
                image_paths.append({
                    "path": filename,
                    "product_name": item["product_name"],
                    "sku": item["sku"],
                    "barcode": barcode_str
                })

            images = [Image.open(ip["path"]) for ip in image_paths]
            total_height = sum(img.height for img in images) + (30 * len(images))
            max_width = max(img.width for img in images)

            combined = Image.new('RGB', (max_width, total_height), 'white')
            y_offset = 0
            for img in images:
                x_offset = (max_width - img.width) // 2
                combined.paste(img, (x_offset, y_offset))
                y_offset += img.height + 30

            save_path, _ = QFileDialog.getSaveFileName(
                self, "Toplu Barkodları Kaydet",
                f"barkodlar_{len(barcode_list)}_adet.png",
                "PNG Dosyası (*.png);;Tüm Dosyalar (*)"
            )
            if save_path:
                combined.save(save_path)
                QMessageBox.information(self, "Başarılı",
                    f"{len(barcode_list)} adet barkod kaydedildi:\n{save_path}")

        except ImportError:
            QMessageBox.warning(
                self, "Eksik Kütüphane",
                "Barkod oluşturmak için 'python-barcode' ve 'Pillow' kütüphaneleri gerekli.\n\n"
                "Kurulum: pip install python-barcode Pillow"
            )
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Toplu barkod oluşturma hatası:\n{str(e)}")

    def render_category(self, value, item):
        if not value:
            return ""
        result = self.category_controller.get_category(value)
        if result["success"] and result["data"]:
            return result["data"]["name"]
        return ""

    def render_brand(self, value, item):
        if not value:
            return ""
        result = self.brand_controller.get_brand(value)
        if result["success"] and result["data"]:
            return result["data"]["name"]
        return ""

    def render_supplier(self, value, item):
        if not value:
            return ""
        result = self.supplier_controller.get_supplier(value)
        if result["success"] and result["data"]:
            return result["data"]["name"]
        return ""

    def render_stock(self, value, item):
        result = self.stock_controller.get_total_stock_by_product(value)
        if result["success"]:
            return str(result["data"])
        return "0"

    def _on_search(self, text: str):
        if not text.strip():
            self.filtered_data = self.data
            self.current_page = 1
            self._update_pagination()
            self._render_table()
            return

        text_lower = text.lower()
        self.filtered_data = []

        for item in self.data:
            if text_lower in (item.get("name", "") or "").lower():
                self.filtered_data.append(item)
                continue

            brand_name = self.render_brand(item.get("brand_ID"), item).lower()
            if text_lower in brand_name:
                self.filtered_data.append(item)
                continue

            supplier_name = self.render_supplier(item.get("supplier_ID"), item).lower()
            if text_lower in supplier_name:
                self.filtered_data.append(item)
                continue

            category_name = self.render_category(item.get("main_category_ID"), item).lower()
            if text_lower in category_name:
                self.filtered_data.append(item)
                continue

            variants_result = self.product_controller.get_product_variants(item["ID"])
            if variants_result["success"]:
                found = False
                for v in variants_result["data"]:
                    sku = (v.get("sku", "") or "").lower()
                    barcode = (v.get("barcode", "") or "").lower()
                    if text_lower in sku or text_lower in barcode:
                        found = True
                        break
                if found:
                    self.filtered_data.append(item)
                    continue

        self.current_page = 1
        self._update_pagination()
        self._render_table()

    def _on_add(self):
        dialog = AddProductDialog(self)
        if dialog.exec_():
            self.refresh_data()

    def _on_edit(self, item):
        dialog = EditProductDialog(self, item)
        if dialog.exec_():
            self.refresh_data()

    def _on_delete(self, item):
        if self.confirm_delete(item.get("name", "")):
            result = self.product_controller.delete_product(item["ID"])
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])


class AddProductDialog(BaseDialog):
    def __init__(self, parent=None):
        self.category_controller = CategoryController()
        self.brand_controller = BrandController()
        self.supplier_controller = SupplierController()
        self.product_controller = ProductController()
        self.images = []
        self._all_categories = {}

        super().__init__(parent, title="Yeni Ürün Ekle", width=700, height=600)

    def _setup_form(self):
        layout = self.form_layout

        form = QFormLayout()
        form.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(self._input_style())
        form.addRow("Ürün Adı *:", self.name_input)

        self.description_input = QLineEdit()
        self.description_input.setStyleSheet(self._input_style())
        form.addRow("Açıklama:", self.description_input)

        self.sale_unit_input = QLineEdit("ADET")
        self.sale_unit_input.setStyleSheet(self._input_style())
        form.addRow("Satış Birimi *:", self.sale_unit_input)

        self.brand_combo = QComboBox()
        self.brand_combo.setStyleSheet(self._input_style())
        brands = self.brand_controller.get_all_brands()
        self.brand_combo.addItem("-- Seçiniz --", None)
        if brands["success"]:
            for b in brands["data"]:
                self.brand_combo.addItem(b["name"], b["ID"])
        form.addRow("Marka *:", self.brand_combo)

        self.supplier_combo = QComboBox()
        self.supplier_combo.setStyleSheet(self._input_style())
        suppliers = self.supplier_controller.get_all_suppliers()
        self.supplier_combo.addItem("-- Seçiniz --", None)
        if suppliers["success"]:
            for s in suppliers["data"]:
                self.supplier_combo.addItem(s["name"], s["ID"])
        form.addRow("Tedarikçi *:", self.supplier_combo)

        layout.addLayout(form)

        cat_label = QLabel("Ana Kategori *:")
        cat_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        layout.addWidget(cat_label)

        self.main_category_tree = QTreeWidget()
        self.main_category_tree.setHeaderHidden(True)
        self.main_category_tree.setFixedHeight(150)
        self.main_category_tree.setStyleSheet(self._input_style())
        layout.addWidget(self.main_category_tree)

        extra_label = QLabel("Ekstra Kategoriler:")
        extra_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        layout.addWidget(extra_label)

        self.extra_category_tree = QTreeWidget()
        self.extra_category_tree.setHeaderHidden(True)
        self.extra_category_tree.setFixedHeight(150)
        self.extra_category_tree.setSelectionMode(QTreeWidget.MultiSelection)
        self.extra_category_tree.setStyleSheet(self._input_style())
        layout.addWidget(self.extra_category_tree)

        cat_result = self.category_controller.get_category_tree()
        if cat_result["success"]:
            self._cache_categories(cat_result["data"])
            self._populate_category_tree(self.main_category_tree, cat_result["data"])
            self._populate_category_tree(self.extra_category_tree, cat_result["data"])

        img_layout = QHBoxLayout()
        self.image_label = QLabel("Henüz resim seçilmedi")
        self.image_label.setStyleSheet(f"color: {Theme.TEXT_MUTED};")
        img_btn = QPushButton("🖼️ Resim Seç")
        img_btn.setStyleSheet(Theme.get_button_style("secondary"))
        img_btn.clicked.connect(self._on_select_images)
        img_layout.addWidget(self.image_label)
        img_layout.addWidget(img_btn)
        layout.addLayout(img_layout)

        save_btn = QPushButton("Kaydet")
        save_btn.setStyleSheet(Theme.get_button_style("primary"))
        save_btn.clicked.connect(self._on_save)
        layout.addWidget(save_btn)

    def _cache_categories(self, nodes):
        for node in nodes:
            self._all_categories[node["ID"]] = node
            if node.get("children"):
                self._cache_categories(node["children"])

    def _populate_category_tree(self, tree_widget: QTreeWidget, nodes: list):
        tree_widget.clear()

        def add_nodes(parent, items):
            for node in items:
                tree_item = QTreeWidgetItem(parent, [node["name"]])
                tree_item.setData(0, Qt.UserRole, node["ID"])
                if node.get("children"):
                    add_nodes(tree_item, node["children"])

        add_nodes(tree_widget, nodes)

    def _collect_parent_ids(self, category_id: int) -> set:
        parent_ids = set()

        def find_parents(nodes, target_id, path):
            for node in nodes:
                current_path = path + [node["ID"]]
                if node["ID"] == target_id:
                    parent_ids.update(path)
                    return True
                if node.get("children") and find_parents(node["children"], target_id, current_path):
                    return True
            return False

        cat_result = self.category_controller.get_category_tree()
        if cat_result["success"]:
            find_parents(cat_result["data"], category_id, [])
        return parent_ids

    def _on_select_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Görselleri Seç", "",
            "Resim Dosyaları (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if files:
            self.images = files
            self.image_label.setText(f"{len(files)} görsel seçildi")

    def _on_save(self):
        name        = self.name_input.text().strip()
        description = self.description_input.text().strip()
        sale_unit   = self.sale_unit_input.text().strip()
        brand_id    = self.brand_combo.currentData()
        supplier_id = self.supplier_combo.currentData()

        main_selected    = self.main_category_tree.selectedItems()
        main_category_id = main_selected[0].data(0, Qt.UserRole) if main_selected else None

        selected_extra_ids = {
            item.data(0, Qt.UserRole)
            for item in self.extra_category_tree.selectedItems()
            if item.data(0, Qt.UserRole) is not None
        }

        if not name:
            QMessageBox.warning(self, "Hata", "Ürün adı zorunludur.")
            return
        if main_category_id is None:
            QMessageBox.warning(self, "Hata", "Lütfen bir ana kategori seçiniz.")
            return
        if brand_id is None:
            QMessageBox.warning(self, "Hata", "Lütfen bir marka seçiniz.")
            return
        if supplier_id is None:
            QMessageBox.warning(self, "Hata", "Lütfen bir tedarikçi seçiniz.")
            return
        if not sale_unit:
            QMessageBox.warning(self, "Hata", "Satış birimi zorunludur.")
            return

        extra_category_ids = set(selected_extra_ids)
        for cat_id in selected_extra_ids:
            extra_category_ids.update(self._collect_parent_ids(cat_id))
        extra_category_ids.update(self._collect_parent_ids(main_category_id))
        extra_category_ids.discard(main_category_id)

        result = self.product_controller.add_product(
            name=name,
            description=description,
            main_category_id=main_category_id,
            extra_category_ids=list(extra_category_ids),
            brand_id=brand_id,
            supplier_id=supplier_id,
            sale_unit=sale_unit
        )

        if not result["success"]:
            QMessageBox.warning(self, "Hata", result["message"])
            return

        product_id = result["product_id"]

        failed_images = []
        for image_path in self.images:
            rel_path, b64_data = save_entity_image(image_path, "products", product_id)
            img_result = self.product_controller.add_product_image(product_id, rel_path, image_data=b64_data)
            if not img_result["success"]:
                failed_images.append(image_path)

        if failed_images:
            QMessageBox.warning(self, "Uyarı",
                f"Ürün eklendi fakat {len(failed_images)} resim kaydedilemedi.")
        else:
            QMessageBox.information(self, "Başarılı", "Ürün başarıyla eklendi.")

        self.accept()

    def _input_style(self) -> str:
        return f"""
            QLineEdit, QComboBox, QTreeWidget, QTableWidget, QSpinBox, QDoubleSpinBox {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.BORDER_RADIUS_SMALL}px;
                padding: 6px 10px;
                font-size: {Theme.FONT_SIZE_NORMAL}px;
            }}
        """


class EditProductDialog(BaseDialog):
    def __init__(self, parent=None, product: dict = None):
        self.product = product
        self.product_controller = ProductController()
        self.category_controller = CategoryController()
        self.brand_controller = BrandController()
        self.supplier_controller = SupplierController()
        self.variant_type_controller = VariantTypeController()
        self._all_categories = {}

        super().__init__(parent, title=f"Ürün Düzenle — {product['name']}", width=900, height=700)

    def _setup_form(self):
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {Theme.BORDER};
                background-color: {Theme.BG_DARK};
            }}
            QTabBar::tab {{
                background-color: {Theme.BG_SIDEBAR};
                color: {Theme.TEXT_SECONDARY};
                padding: 8px 20px;
                border: 1px solid {Theme.BORDER};
            }}
            QTabBar::tab:selected {{
                background-color: {Theme.BG_DARK};
                color: {Theme.TEXT_PRIMARY};
                border-bottom: 2px solid {Theme.ACCENT};
            }}
        """)

        tabs.addTab(self._build_general_tab(),        "📋 Genel Bilgiler")
        tabs.addTab(self._build_general_images_tab(), "🖼️ Genel Resimler")
        tabs.addTab(self._build_variants_tab(),       "📦 Varyantlar")
        tabs.addTab(self._build_variant_images_tab(), "🎨 Varyant Resimleri")

        self.form_layout.addWidget(tabs)

    def _build_general_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(10)

        self.edit_name = QLineEdit(self.product.get("name", ""))
        self.edit_name.setStyleSheet(self._input_style())
        form.addRow("Ürün Adı *:", self.edit_name)

        self.edit_description = QLineEdit(self.product.get("description", ""))
        self.edit_description.setStyleSheet(self._input_style())
        form.addRow("Açıklama:", self.edit_description)

        self.edit_sale_unit = QLineEdit(self.product.get("sale_unit", "ADET"))
        self.edit_sale_unit.setStyleSheet(self._input_style())
        form.addRow("Satış Birimi *:", self.edit_sale_unit)

        self.edit_brand_combo = QComboBox()
        self.edit_brand_combo.setStyleSheet(self._input_style())
        self.edit_brand_combo.addItem("-- Seçiniz --", None)
        brands = self.brand_controller.get_all_brands()
        if brands["success"]:
            for b in brands["data"]:
                self.edit_brand_combo.addItem(b["name"], b["ID"])
                if b["ID"] == self.product.get("brand_ID"):
                    self.edit_brand_combo.setCurrentIndex(self.edit_brand_combo.count() - 1)
        form.addRow("Marka *:", self.edit_brand_combo)

        self.edit_supplier_combo = QComboBox()
        self.edit_supplier_combo.setStyleSheet(self._input_style())
        self.edit_supplier_combo.addItem("-- Seçiniz --", None)
        suppliers = self.supplier_controller.get_all_suppliers()
        if suppliers["success"]:
            for s in suppliers["data"]:
                self.edit_supplier_combo.addItem(s["name"], s["ID"])
                if s["ID"] == self.product.get("supplier_ID"):
                    self.edit_supplier_combo.setCurrentIndex(self.edit_supplier_combo.count() - 1)
        form.addRow("Tedarikçi *:", self.edit_supplier_combo)

        self.edit_active_combo = QComboBox()
        self.edit_active_combo.setStyleSheet(self._input_style())
        self.edit_active_combo.addItem("Aktif", 1)
        self.edit_active_combo.addItem("Pasif", 0)
        self.edit_active_combo.setCurrentIndex(0 if self.product.get("is_active") else 1)
        form.addRow("Durum:", self.edit_active_combo)

        layout.addLayout(form)

        cat_result = self.category_controller.get_category_tree()
        cat_data = cat_result["data"] if cat_result["success"] else []
        self._cache_categories(cat_data)

        import json
        current_main   = self.product.get("main_category_ID")
        current_extras = json.loads(self.product.get("extra_category_IDs", "[]") or "[]")

        main_label = QLabel("Ana Kategori *:")
        main_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        layout.addWidget(main_label)

        self.edit_main_cat_tree = QTreeWidget()
        self.edit_main_cat_tree.setHeaderHidden(True)
        self.edit_main_cat_tree.setFixedHeight(130)
        self.edit_main_cat_tree.setStyleSheet(self._input_style())
        self._populate_category_tree(self.edit_main_cat_tree, cat_data, select_id=current_main)
        layout.addWidget(self.edit_main_cat_tree)

        extra_label = QLabel("Ekstra Kategoriler:")
        extra_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        layout.addWidget(extra_label)

        self.edit_extra_cat_tree = QTreeWidget()
        self.edit_extra_cat_tree.setHeaderHidden(True)
        self.edit_extra_cat_tree.setFixedHeight(130)
        self.edit_extra_cat_tree.setSelectionMode(QTreeWidget.MultiSelection)
        self.edit_extra_cat_tree.setStyleSheet(self._input_style())
        self._populate_category_tree(self.edit_extra_cat_tree, cat_data, select_ids=current_extras)
        layout.addWidget(self.edit_extra_cat_tree)

        save_btn = QPushButton("💾 Değişiklikleri Kaydet")
        save_btn.setStyleSheet(Theme.get_button_style("primary"))
        save_btn.clicked.connect(self._on_save_general)
        layout.addWidget(save_btn)

        layout.addStretch()
        return widget

    def _on_save_general(self):
        name        = self.edit_name.text().strip()
        description = self.edit_description.text().strip()
        sale_unit   = self.edit_sale_unit.text().strip()
        brand_id    = self.edit_brand_combo.currentData()
        supplier_id = self.edit_supplier_combo.currentData()
        is_active   = self.edit_active_combo.currentData()

        main_selected    = self.edit_main_cat_tree.selectedItems()
        main_category_id = main_selected[0].data(0, Qt.UserRole) if main_selected else None

        selected_extra_ids = {
            item.data(0, Qt.UserRole)
            for item in self.edit_extra_cat_tree.selectedItems()
            if item.data(0, Qt.UserRole) is not None
        }

        if not name:
            QMessageBox.warning(self, "Hata", "Ürün adı zorunludur.")
            return
        if main_category_id is None:
            QMessageBox.warning(self, "Hata", "Lütfen bir ana kategori seçiniz.")
            return
        if brand_id is None:
            QMessageBox.warning(self, "Hata", "Lütfen bir marka seçiniz.")
            return
        if supplier_id is None:
            QMessageBox.warning(self, "Hata", "Lütfen bir tedarikçi seçiniz.")
            return
        if not sale_unit:
            QMessageBox.warning(self, "Hata", "Satış birimi zorunludur.")
            return

        import json
        extra_category_ids = set(selected_extra_ids)
        for cat_id in selected_extra_ids:
            extra_category_ids.update(self._collect_parent_ids(cat_id))
        extra_category_ids.update(self._collect_parent_ids(main_category_id))
        extra_category_ids.discard(main_category_id)

        result = self.product_controller.update_product(self.product["ID"], {
            "name": name,
            "description": description,
            "sale_unit": sale_unit.upper(),
            "brand_ID": brand_id,
            "supplier_ID": supplier_id,
            "is_active": is_active,
            "main_category_ID": main_category_id,
            "extra_category_IDs": json.dumps(list(extra_category_ids))
        })

        if result["success"]:
            QMessageBox.information(self, "Başarılı", "Ürün güncellendi.")
            self.product["name"] = name
        else:
            QMessageBox.warning(self, "Hata", result["message"])

    def _build_general_images_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("🖼️ Resim Ekle")
        add_btn.setStyleSheet(Theme.get_button_style("primary"))
        add_btn.clicked.connect(self._on_add_general_image)
        btn_layout.addWidget(add_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"background-color: {Theme.BG_DARK}; border: none;")
        self.general_images_container = QWidget()
        self.general_images_grid = QGridLayout(self.general_images_container)
        self.general_images_grid.setSpacing(12)
        scroll.setWidget(self.general_images_container)
        layout.addWidget(scroll)

        self._refresh_general_images()
        return widget

    def _refresh_general_images(self):
        result = self.product_controller.get_general_product_images(self.product["ID"])
        images = result["data"] if result["success"] else []

        while self.general_images_grid.count():
            child = self.general_images_grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for i, img in enumerate(images):
            card = self._create_image_card(img["image_path"], img["ID"], "general", img.get("image_data", ""))
            row = i // 3
            col = i % 3
            self.general_images_grid.addWidget(card, row, col)

    def _on_add_general_image(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Resim Seç", "",
            "Resim Dosyaları (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        for f in files:
            rel_path, b64_data = save_entity_image(f, "products", self.product["ID"])
            self.product_controller.add_product_image(self.product["ID"], rel_path, variant_id=None, image_data=b64_data)
        self._refresh_general_images()

    def _on_delete_image(self, image_id: int, image_type: str):
        result = self.product_controller.delete_product_image(image_id)
        if result["success"]:
            if image_type == "general":
                self._refresh_general_images()
            else:
                self._refresh_variant_images()
        else:
            QMessageBox.warning(self, "Hata", result["message"])

    def _build_variants_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("+ Varyant Ekle")
        add_btn.setStyleSheet(Theme.get_button_style("primary"))
        add_btn.clicked.connect(self._on_add_variant)
        btn_layout.addWidget(add_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.variants_table = QTableWidget()
        self.variants_table.setColumnCount(7)
        self.variants_table.setHorizontalHeaderLabels([
            "SKU", "Barkod", "Alış Fiyatı", "Satış Fiyatı", "Attributelar", "Düzenle", "Sil"
        ])
        header = self.variants_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        self.variants_table.setColumnWidth(5, 100)
        self.variants_table.setColumnWidth(6, 90)
        self.variants_table.verticalHeader().setDefaultSectionSize(40)
        self.variants_table.setStyleSheet(self._input_style())
        layout.addWidget(self.variants_table)

        self._refresh_variants()
        return widget

    def _refresh_variants(self):
        result = self.product_controller.get_product_variants(self.product["ID"])
        variants = result["data"] if result["success"] else []
        self.variants_table.setRowCount(0)

        for v in variants:
            row = self.variants_table.rowCount()
            self.variants_table.insertRow(row)
            self.variants_table.setItem(row, 0, QTableWidgetItem(v.get("sku", "")))
            self.variants_table.setItem(row, 1, QTableWidgetItem(v.get("barcode", "")))
            self.variants_table.setItem(row, 2, QTableWidgetItem(str(v.get("buy_price", 0))))
            self.variants_table.setItem(row, 3, QTableWidgetItem(str(v.get("sell_price", 0))))

            attrs_result = self.product_controller.get_variant_attributes(v["ID"])
            attr_text = ""
            if attrs_result["success"] and attrs_result["data"]:
                attr_text = ", ".join(
                    f"{a['type_name']}: {a['value']}" for a in attrs_result["data"]
                )
            self.variants_table.setItem(row, 4, QTableWidgetItem(attr_text))

            edit_btn = QPushButton("Düzenle")
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.setFixedSize(80, 28)
            edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.INFO};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0 8px;
                }}
                QPushButton:hover {{
                    background-color: #5bc7e0;
                }}
            """)
            edit_btn.clicked.connect(lambda _, variant=v: self._on_edit_variant(variant))
            self.variants_table.setCellWidget(row, 5, edit_btn)

            del_btn = QPushButton("Sil")
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setFixedSize(60, 28)
            del_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.ERROR};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0 8px;
                }}
                QPushButton:hover {{
                    background-color: #ff8a8a;
                }}
            """)
            del_btn.clicked.connect(lambda _, vid=v["ID"]: self._on_delete_variant(vid))
            self.variants_table.setCellWidget(row, 6, del_btn)

    def _on_add_variant(self):
        dialog = AddVariantDialog(self, product_id=self.product["ID"])
        if dialog.exec_():
            self._refresh_variants()
            self._refresh_variant_images_combo()

    def _on_edit_variant(self, variant: dict):
        dialog = AddVariantDialog(self, product_id=self.product["ID"], variant=variant)
        if dialog.exec_():
            self._refresh_variants()

    def _on_delete_variant(self, variant_id: int):
        reply = QMessageBox.question(
            self, "Onay", "Bu varyantı silmek istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            result = self.product_controller.delete_variant(variant_id)
            if result["success"]:
                self._refresh_variants()
                self._refresh_variant_images_combo()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _build_variant_images_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        combo_layout = QHBoxLayout()
        combo_label = QLabel("Varyant:")
        combo_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        self.variant_images_combo = QComboBox()
        self.variant_images_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.BORDER_RADIUS_SMALL}px;
                padding: 6px 10px;
                font-size: {Theme.FONT_SIZE_NORMAL}px;
                min-width: 250px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Theme.BG_SIDEBAR};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                selection-background-color: {Theme.BG_HOVER};
                selection-color: {Theme.TEXT_PRIMARY};
                outline: none;
            }}
            QComboBox::drop-down {{
                border: none;
                background-color: {Theme.BG_INPUT};
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
        """)
        self.variant_images_combo.currentIndexChanged.connect(self._refresh_variant_images)
        combo_layout.addWidget(combo_label)
        combo_layout.addWidget(self.variant_images_combo)
        combo_layout.addStretch()
        layout.addLayout(combo_layout)

        add_btn = QPushButton("🖼️ Bu Varyanta Resim Ekle")
        add_btn.setStyleSheet(Theme.get_button_style("primary"))
        add_btn.clicked.connect(self._on_add_variant_image)
        layout.addWidget(add_btn)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"background-color: {Theme.BG_DARK}; border: none;")
        self.variant_images_container = QWidget()
        self.variant_images_grid = QGridLayout(self.variant_images_container)
        self.variant_images_grid.setSpacing(12)
        scroll.setWidget(self.variant_images_container)
        layout.addWidget(scroll)

        self._refresh_variant_images_combo()
        return widget

    def _refresh_variant_images_combo(self):
        self.variant_images_combo.clear()
        result = self.product_controller.get_product_variants(self.product["ID"])
        if result["success"] and result["data"]:
            for v in result["data"]:
                label = f"{v['sku']} — {v['barcode']}"
                self.variant_images_combo.addItem(label, v["ID"])
        else:
            self.variant_images_combo.addItem("Henüz varyant yok", None)

    def _refresh_variant_images(self):
        variant_id = self.variant_images_combo.currentData()

        while self.variant_images_grid.count():
            child = self.variant_images_grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not variant_id:
            return

        result = self.product_controller.get_variant_images(variant_id)
        images = result["data"] if result["success"] else []

        for i, img in enumerate(images):
            card = self._create_image_card(img["image_path"], img["ID"], "variant", img.get("image_data", ""))
            row = i // 3
            col = i % 3
            self.variant_images_grid.addWidget(card, row, col)

    def _on_add_variant_image(self):
        variant_id = self.variant_images_combo.currentData()
        if not variant_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir varyant seçiniz.")
            return

        files, _ = QFileDialog.getOpenFileNames(
            self, "Resim Seç", "",
            "Resim Dosyaları (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        for f in files:
            rel_path, b64_data = save_entity_image(f, "products", self.product["ID"])
            self.product_controller.add_product_image(self.product["ID"], rel_path, variant_id=variant_id, image_data=b64_data)
        self._refresh_variant_images()

    def _create_image_card(self, image_path: str, image_id: int, image_type: str, image_data: str = None) -> QFrame:
        resolved = resolve_image_path(image_path, image_data)
        display_path = resolved or image_path

        card = QFrame()
        card.setFixedSize(160, 210)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(5, 5, 5, 5)
        card_layout.setSpacing(5)

        img_label = QLabel()
        img_label.setFixedSize(148, 148)
        img_label.setAlignment(Qt.AlignCenter)
        img_label.setCursor(Qt.PointingHandCursor)
        img_label.setToolTip("Çift tıkla → büyük göster")
        img_label.setStyleSheet("border: none;")

        if resolved:
            pixmap = QPixmap(resolved)
            if not pixmap.isNull():
                scaled = pixmap.scaled(148, 148, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_label.setPixmap(scaled)
            else:
                img_label.setText("❌ Yüklenemedi")
                img_label.setStyleSheet(f"color: {Theme.ERROR}; border: none;")
        else:
            img_label.setText("❌ Yüklenemedi")
            img_label.setStyleSheet(f"color: {Theme.ERROR}; border: none;")

        img_label.mouseDoubleClickEvent = lambda e, p=display_path: self._show_full_image(p)
        card_layout.addWidget(img_label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        open_btn = QPushButton("🔍")
        open_btn.setFixedSize(40, 28)
        open_btn.setToolTip("Büyük göster")
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.setStyleSheet(Theme.get_button_style("secondary"))
        open_btn.clicked.connect(lambda _, p=display_path: self._show_full_image(p))
        btn_layout.addWidget(open_btn)

        del_btn = QPushButton("🗑️ Sil")
        del_btn.setFixedHeight(28)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet(Theme.get_button_style("danger"))
        del_btn.clicked.connect(lambda _, iid=image_id: self._on_delete_image(iid, image_type))
        btn_layout.addWidget(del_btn)

        card_layout.addLayout(btn_layout)

        return card

    def _show_full_image(self, image_path: str):
        dialog = QDialog(self)
        dialog.setWindowTitle("Resim Önizleme")
        dialog.setMinimumSize(800, 600)
        dialog.setStyleSheet(f"background-color: {Theme.BG_DARK};")

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(10, 10, 10, 10)

        img_label = QLabel()
        img_label.setAlignment(Qt.AlignCenter)

        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            screen_size = dialog.screen().availableGeometry()
            max_w = int(screen_size.width() * 0.8)
            max_h = int(screen_size.height() * 0.8)
            scaled = pixmap.scaled(max_w, max_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_label.setPixmap(scaled)
            dialog.resize(scaled.width() + 20, scaled.height() + 80)
        else:
            img_label.setText("❌ Resim yüklenemedi")
            img_label.setStyleSheet(f"color: {Theme.ERROR}; font-size: 18px;")

        layout.addWidget(img_label)

        path_label = QLabel(image_path)
        path_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px;")
        path_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(path_label)

        close_btn = QPushButton("Kapat")
        close_btn.setFixedSize(120, 36)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(Theme.get_button_style("secondary"))
        close_btn.clicked.connect(dialog.close)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        dialog.exec_()

    def _cache_categories(self, nodes):
        for node in nodes:
            self._all_categories[node["ID"]] = node
            if node.get("children"):
                self._cache_categories(node["children"])

    def _populate_category_tree(self, tree_widget: QTreeWidget, nodes: list,
                                 select_id: int = None, select_ids: list = None):
        tree_widget.clear()

        def add_nodes(parent, items):
            for node in items:
                tree_item = QTreeWidgetItem(parent, [node["name"]])
                tree_item.setData(0, Qt.UserRole, node["ID"])
                if select_id is not None and select_ids is None and node["ID"] == select_id:
                    tree_item.setSelected(True)
                if select_ids is not None and select_id is None and node["ID"] in select_ids:
                    tree_item.setSelected(True)
                if node.get("children"):
                    add_nodes(tree_item, node["children"])

        add_nodes(tree_widget, nodes)

    def _collect_parent_ids(self, category_id: int) -> set:
        parent_ids = set()

        def find_parents(nodes, target_id, path):
            for node in nodes:
                current_path = path + [node["ID"]]
                if node["ID"] == target_id:
                    parent_ids.update(path)
                    return True
                if node.get("children") and find_parents(node["children"], target_id, current_path):
                    return True
            return False

        cat_result = self.category_controller.get_category_tree()
        if cat_result["success"]:
            find_parents(cat_result["data"], category_id, [])
        return parent_ids

    def _input_style(self) -> str:
        return f"""
            QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.BORDER_RADIUS_SMALL}px;
                padding: 6px 10px;
                font-size: {Theme.FONT_SIZE_NORMAL}px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Theme.BG_SIDEBAR};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                selection-background-color: {Theme.BG_HOVER};
                selection-color: {Theme.TEXT_PRIMARY};
                outline: none;
            }}
            QComboBox::drop-down {{
                border: none;
                background-color: {Theme.BG_INPUT};
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
            QTreeWidget {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.BORDER_RADIUS_SMALL}px;
            }}
            QTableWidget {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                gridline-color: {Theme.BORDER};
            }}
            QTableWidget::item {{
                color: {Theme.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {Theme.BG_SIDEBAR};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                padding: 4px;
            }}
        """


class AddVariantDialog(BaseDialog):
    def __init__(self, parent=None, product_id: int = None, variant: dict = None):
        self.product_id = product_id
        self.variant = variant
        self.product_controller = ProductController()
        self.variant_type_controller = VariantTypeController()
        self.attribute_rows = []

        title = "Varyant Düzenle" if variant else "Yeni Varyant Ekle"
        super().__init__(parent, title=title, width=600, height=550)

    def _setup_form(self):
        layout = self.form_layout
        form = QFormLayout()
        form.setSpacing(10)

        self.sku_input = QLineEdit(self.variant.get("sku", "") if self.variant else "")
        self.sku_input.setStyleSheet(self._input_style())
        form.addRow("SKU *:", self.sku_input)

        self.barcode_input = QLineEdit(self.variant.get("barcode", "") if self.variant else "")
        self.barcode_input.setStyleSheet(self._input_style())
        form.addRow("Barkod *:", self.barcode_input)

        self.buy_price_input = QDoubleSpinBox()
        self.buy_price_input.setRange(0, 9999999)
        self.buy_price_input.setDecimals(2)
        self.buy_price_input.setValue(self.variant.get("buy_price", 0) if self.variant else 0)
        self.buy_price_input.setStyleSheet(self._input_style())
        form.addRow("Alış Fiyatı *:", self.buy_price_input)

        self.sell_price_input = QDoubleSpinBox()
        self.sell_price_input.setRange(0, 9999999)
        self.sell_price_input.setDecimals(2)
        self.sell_price_input.setValue(self.variant.get("sell_price", 0) if self.variant else 0)
        self.sell_price_input.setStyleSheet(self._input_style())
        form.addRow("Satış Fiyatı *:", self.sell_price_input)

        self.vat_included_check = QCheckBox("KDV Dahil")
        self.vat_included_check.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        self.vat_included_check.setChecked(bool(self.variant.get("vat_included", False)) if self.variant else False)
        form.addRow("", self.vat_included_check)

        self.vat_rate_input = QDoubleSpinBox()
        self.vat_rate_input.setRange(0, 100)
        self.vat_rate_input.setDecimals(1)
        self.vat_rate_input.setValue(self.variant.get("vat_rate", 0) if self.variant else 0)
        self.vat_rate_input.setStyleSheet(self._input_style())
        form.addRow("KDV Oranı (%):", self.vat_rate_input)

        layout.addLayout(form)

        attr_label = QLabel("Özellikler (Attribute):")
        attr_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-weight: bold;")
        layout.addWidget(attr_label)

        self.attr_container = QVBoxLayout()
        layout.addLayout(self.attr_container)

        if self.variant:
            attrs_result = self.product_controller.get_variant_attributes(self.variant["ID"])
            if attrs_result["success"] and attrs_result["data"]:
                for a in attrs_result["data"]:
                    self._add_attribute_row(
                        selected_type_id=a["variant_type_ID"],
                        selected_value_id=a["ID"]
                    )

        add_attr_btn = QPushButton("+ Özellik Ekle")
        add_attr_btn.setStyleSheet(Theme.get_button_style("secondary"))
        add_attr_btn.clicked.connect(lambda: self._add_attribute_row())
        layout.addWidget(add_attr_btn)

    def _add_attribute_row(self, selected_type_id: int = None, selected_value_id: int = None):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        type_combo = QComboBox()
        type_combo.setStyleSheet(self._input_style())
        type_combo.setFixedWidth(160)

        value_combo = QComboBox()
        value_combo.setStyleSheet(self._input_style())
        value_combo.setFixedWidth(160)

        types_result = self.variant_type_controller.get_all_types_with_values()
        types_data = types_result["data"] if types_result["success"] else []

        type_combo.addItem("-- Tip Seç --", None)
        for t in types_data:
            type_combo.addItem(t["name"], t["ID"])

        def on_type_changed(index, tc=type_combo, vc=value_combo):
            vc.clear()
            vc.addItem("-- Değer Seç --", None)
            type_id = tc.currentData()
            if type_id is None:
                return
            for t in types_data:
                if t["ID"] == type_id:
                    for val in t["values"]:
                        vc.addItem(val["value"], val["ID"])
                    break

        type_combo.currentIndexChanged.connect(on_type_changed)

        if selected_type_id is not None:
            for i in range(type_combo.count()):
                if type_combo.itemData(i) == selected_type_id:
                    type_combo.setCurrentIndex(i)
                    break
            value_combo.clear()
            value_combo.addItem("-- Değer Seç --", None)
            for t in types_data:
                if t["ID"] == selected_type_id:
                    for val in t["values"]:
                        value_combo.addItem(val["value"], val["ID"])
                    break
            if selected_value_id is not None:
                for i in range(value_combo.count()):
                    if value_combo.itemData(i) == selected_value_id:
                        value_combo.setCurrentIndex(i)
                        break

        del_btn = QPushButton("−")
        del_btn.setFixedSize(30, 30)
        del_btn.setStyleSheet(Theme.get_button_style("danger"))

        row_layout.addWidget(type_combo)
        row_layout.addWidget(value_combo)
        row_layout.addWidget(del_btn)
        row_layout.addStretch()

        self.attr_container.addWidget(row_widget)
        row_data = (type_combo, value_combo, row_widget)
        self.attribute_rows.append(row_data)

        del_btn.clicked.connect(lambda _, rd=row_data: self._remove_attribute_row(rd))

    def _remove_attribute_row(self, row_data):
        type_combo, value_combo, row_widget = row_data
        row_widget.setParent(None)
        row_widget.deleteLater()
        self.attribute_rows.remove(row_data)

    def _on_save(self):
        sku        = self.sku_input.text().strip()
        barcode    = self.barcode_input.text().strip()
        buy_price  = self.buy_price_input.value()
        sell_price = self.sell_price_input.value()
        vat_included = self.vat_included_check.isChecked()
        vat_rate   = self.vat_rate_input.value()

        if not sku:
            QMessageBox.warning(self, "Hata", "SKU zorunludur.")
            return
        if not barcode:
            QMessageBox.warning(self, "Hata", "Barkod zorunludur.")
            return

        value_ids = []
        for type_combo, value_combo, _ in self.attribute_rows:
            type_id  = type_combo.currentData()
            value_id = value_combo.currentData()
            if type_id is None or value_id is None:
                QMessageBox.warning(self, "Hata", "Lütfen tüm özellik satırlarını doldurunuz.")
                return
            value_ids.append(value_id)

        if self.variant:
            result = self.product_controller.update_variant(
                variant_id=self.variant["ID"],
                data={
                    "sku": sku,
                    "barcode": barcode,
                    "buy_price": buy_price,
                    "sell_price": sell_price,
                    "vat_included": int(vat_included),
                    "vat_rate": vat_rate,
                },
                attribute_value_ids=value_ids
            )
        else:
            result = self.product_controller.add_variant(
                product_id=self.product_id,
                sku=sku,
                barcode=barcode,
                buy_price=buy_price,
                sell_price=sell_price,
                vat_included=vat_included,
                vat_rate=vat_rate,
                attribute_value_ids=value_ids
            )

        if result["success"]:
            QMessageBox.information(self, "Başarılı",
                "Varyant güncellendi." if self.variant else "Varyant eklendi.")
            self.accept()
        else:
            QMessageBox.warning(self, "Hata", result["message"])

    def _input_style(self) -> str:
        return f"""
            QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.BORDER_RADIUS_SMALL}px;
                padding: 6px 10px;
                font-size: {Theme.FONT_SIZE_NORMAL}px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Theme.BG_SIDEBAR};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                selection-background-color: {Theme.BG_HOVER};
                selection-color: {Theme.TEXT_PRIMARY};
                outline: none;
            }}
            QComboBox::drop-down {{
                border: none;
                background-color: {Theme.BG_INPUT};
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
        """