import json
from PyQt5.QtWidgets import (QLineEdit, QComboBox, QMessageBox, QLabel,
                              QPushButton, QTextEdit, QMenu, QAction,
                              QHBoxLayout, QVBoxLayout, QWidget, QSpinBox,
                              QDoubleSpinBox, QTableWidget, QTableWidgetItem,
                              QHeaderView, QFrame, QAbstractItemView,
                              QDialog, QScrollArea, QCompleter, QCheckBox,
                              QInputDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from views.base_list_view import BaseListView
from views.base_dialog import BaseDialog
from controllers.order_controller import OrderController
from database.customer_repository import CustomerRepository
from database.product_repository import ProductRepository
from database.variant_repository import VariantRepository
from database.location_repository import LocationRepository
from database.order_item_repository import OrderItemRepository
from database.payment_repository import PaymentRepository
from utils.theme import Theme
from utils.permission_helper import has_permission


STATUS_MAP = {
    "pending": ("Beklemede", Theme.WARNING),
    "confirmed": ("Onaylandı", Theme.INFO),
    "preparing": ("Hazırlanıyor", Theme.INFO),
    "shipped": ("Kargoda", "#a78bfa"),
    "delivered": ("Teslim Edildi", Theme.SUCCESS),
    "completed": ("Tamamlandı", Theme.SUCCESS),
    "cancelled": ("İptal", Theme.ERROR),
}

PAYMENT_METHOD_MAP = {
    "cash": "Nakit",
    "credit_card": "Kredi Kartı",
    "debit_card": "Banka Kartı",
    "bank_transfer": "Havale/EFT",
    "other": "Diğer",
}


def _input_style():
    return f"""
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
            background-color: {Theme.BG_INPUT};
            color: {Theme.TEXT_PRIMARY};
            border: 1px solid {Theme.BORDER};
            border-radius: 6px;
            padding: 0 12px;
            font-size: 13px;
        }}
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 1px solid {Theme.BORDER_FOCUS};
        }}
    """


def _table_style():
    return f"""
        QTableWidget {{
            background-color: {Theme.BG_INPUT};
            color: {Theme.TEXT_PRIMARY};
            border: 1px solid {Theme.BORDER};
            border-radius: 6px;
            gridline-color: {Theme.BORDER};
            font-size: 12px;
        }}
        QHeaderView::section {{
            background-color: {Theme.BG_SIDEBAR};
            color: {Theme.TEXT_SECONDARY};
            border: none;
            border-bottom: 1px solid {Theme.BORDER};
            padding: 6px;
            font-size: 11px;
            font-weight: bold;
        }}
    """


def _make_searchable(combo: QComboBox):
    combo.setEditable(True)
    combo.setInsertPolicy(QComboBox.NoInsert)
    completer = combo.completer()
    if completer:
        completer.setFilterMode(Qt.MatchContains)
        completer.setCompletionMode(QCompleter.PopupCompletion)


class OrdersView(BaseListView):
    def __init__(self):
        self.controller = OrderController()
        self.customer_repo = CustomerRepository()
        self.order_item_repo = OrderItemRepository()
        self.payment_repo = PaymentRepository()

        columns = [
            {"key": "ID", "title": "Sipariş No", "width": 90, "align": "center"},
            {
                "key": "customer_ID", "title": "Müşteri", "width": 160,
                "render": lambda val, item: self._get_customer_name(val)
            },
            {
                "key": "ID", "title": "Kalem", "width": 60, "align": "center",
                "render": lambda val, item: str(len(self.order_item_repo.get_by_order(val)))
            },
            {
                "key": "ID", "title": "Tutar", "width": 110, "align": "right",
                "render": lambda val, item: self._get_order_total(val, item)
            },
            {
                "key": "ID", "title": "Ödenen", "width": 110, "align": "right",
                "render": lambda val, item: f"{self.payment_repo.get_order_paid_total(val):,.2f} ₺"
            },
            {
                "key": "status", "title": "Durum", "width": 110, "align": "center",
                "render": lambda val, item: STATUS_MAP.get(val, (val, ""))[0]
            },
            {"key": "created_at", "title": "Tarih", "width": 140, "align": "center",
             "render": lambda val, item: val[:16] if val else "-"},
        ]

        super().__init__(
            title="Sipariş Yönetimi",
            columns=columns,
            add_permission="order_create",
            edit_permission="order_update",
            delete_permission="order_delete"
        )

        self.add_btn.setText("+ Yeni Sipariş")

        self.status_filter = QComboBox()
        self.status_filter.setFixedHeight(34)
        self.status_filter.setFixedWidth(160)
        self.status_filter.setStyleSheet(f"""
            QComboBox {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 0 10px;
                font-size: 13px;
            }}
            QComboBox:focus {{ border: 1px solid {Theme.BORDER_FOCUS}; }}
            QComboBox::drop-down {{ border: none; width: 24px; }}
            QComboBox::down-arrow {{ image: none; border: none; }}
            QComboBox QAbstractItemView {{
                background-color: {Theme.BG_CARD};
                color: {Theme.TEXT_PRIMARY};
                selection-background-color: {Theme.BG_HOVER};
                border: 1px solid {Theme.BORDER};
            }}
        """)
        self.status_filter.addItem("Tüm Durumlar", None)
        for key, (label, _) in STATUS_MAP.items():
            self.status_filter.addItem(label, key)
        self.status_filter.currentIndexChanged.connect(self._on_filter_changed)
        self.filter_layout.insertWidget(self.filter_layout.count() - 1, self.status_filter)

        self._setup_context_menu()
        self.refresh_data()


    def _get_customer_name(self, customer_id) -> str:
        if not customer_id or customer_id == 0:
            return "Mağaza Müşterisi"
        try:
            customer = self.customer_repo.get_by_id(customer_id)
            if customer:
                return f"{customer['first_name']} {customer['last_name']}"
        except Exception:
            pass
        return "—"

    def _get_order_total(self, order_id, item) -> str:
        try:
            total = self.order_item_repo.get_order_total(order_id)
            discount = item.get("discount_price", 0.0) or 0.0
            net = total - discount
            return f"{net:,.2f} ₺"
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
        status = item.get("status", "pending")

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

        detail_action = QAction("📋 Detay Görüntüle", self)
        detail_action.triggered.connect(lambda: self._show_order_detail(item))
        menu.addAction(detail_action)
        menu.addSeparator()

        if status != "cancelled":
            status_menu = menu.addMenu("📊 Durum Güncelle")
            status_menu.setStyleSheet(menu.styleSheet())
            for key, (label, _) in STATUS_MAP.items():
                if key != status:
                    action = QAction(label, self)
                    action.triggered.connect(lambda checked, s=key: self._update_status(item, s))
                    status_menu.addAction(action)
            menu.addSeparator()

        if status not in ("cancelled", "completed", "delivered"):
            edit_items_action = QAction("📝 Kalemleri Düzenle", self)
            edit_items_action.triggered.connect(lambda: self._edit_order_items(item))
            menu.addAction(edit_items_action)

        if status != "cancelled":
            payment_action = QAction("💳 Ödeme Ekle", self)
            payment_action.triggered.connect(lambda: self._add_payment(item))
            menu.addAction(payment_action)

        if status != "cancelled":
            discount_action = QAction("🏷️ İndirim Uygula", self)
            discount_action.triggered.connect(lambda: self._apply_discount(item))
            menu.addAction(discount_action)

        menu.addSeparator()

        if status != "cancelled":
            refund_action = QAction("↩️ İade İşlemi", self)
            refund_action.triggered.connect(lambda: self._refund_order(item))
            menu.addAction(refund_action)

        if status not in ("cancelled", "completed", "delivered"):
            cancel_action = QAction("❌ Sipariş İptal", self)
            cancel_action.triggered.connect(lambda: self._cancel_order(item))
            menu.addAction(cancel_action)

        menu.exec_(self.table.viewport().mapToGlobal(pos))


    def _update_status(self, item: dict, new_status: str):
        result = self.controller.update_order_status(item["ID"], new_status)
        if result["success"]:
            self.refresh_data()
        else:
            QMessageBox.warning(self, "Hata", result["message"])

    def _cancel_order(self, item: dict):
        reply = QMessageBox.question(
            self, "Sipariş İptali",
            f"Sipariş #{item['ID']} iptal edilsin mi?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            result = self.controller.cancel_order(item["ID"], reason="Kullanıcı tarafından iptal")
            if result["success"]:
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _add_payment(self, item: dict):
        dialog = AddPaymentDialog(self, order=item)
        if dialog.exec_() == AddPaymentDialog.Accepted:
            data = dialog.result_data
            result = self.controller.add_payment(
                order_id=item["ID"], method=data["method"],
                amount=data["amount"], note=data.get("note", "")
            )
            if result["success"]:
                QMessageBox.information(self, "Başarılı", result["message"])
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _show_order_detail(self, item: dict):
        dialog = OrderDetailDialog(self, order_id=item["ID"])
        dialog.exec_()
        self.refresh_data()

    def _edit_order_items(self, item: dict):
        dialog = EditOrderItemsDialog(self, order_id=item["ID"])
        dialog.exec_()
        self.refresh_data()

    def _apply_discount(self, item: dict):
        dialog = DiscountDialog(self, order=item)
        if dialog.exec_() == DiscountDialog.Accepted:
            result = self.controller.update_order_discount(item["ID"], dialog.result_data["discount"])
            if result["success"]:
                QMessageBox.information(self, "Başarılı", result["message"])
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Hata", result["message"])

    def _refund_order(self, item: dict):
        dialog = RefundDialog(self, order_id=item["ID"])
        if dialog.exec_() == RefundDialog.Accepted:
            self.refresh_data()


    def _on_filter_changed(self):
        self._apply_filters()

    def _on_search(self, text: str):
        self._apply_filters()

    def _apply_filters(self):
        search_text = self.search_input.text().strip().lower()
        status_filter = self.status_filter.currentData()

        self.filtered_data = []
        for item in self.data:
            if status_filter and item.get("status") != status_filter:
                continue
            if search_text:
                order_id_str = str(item.get("ID", ""))
                customer_name = self._get_customer_name(item.get("customer_ID", 0)).lower()
                notes = str(item.get("notes", "")).lower()
                if not any(search_text in f for f in [order_id_str, customer_name, notes]):
                    continue
            self.filtered_data.append(item)

        self.current_page = 1
        self._update_pagination()
        self._render_table()


    def refresh_data(self):
        result = self.controller.get_all_orders()
        if result["success"]:
            data = sorted(result["data"], key=lambda x: x.get("ID", 0), reverse=True)
            self.set_data(data)

    def _on_add(self):
        dialog = CreateOrderDialog(self)
        if dialog.exec_() == CreateOrderDialog.Accepted:
            self.refresh_data()

    def _on_edit(self, item: dict):
        self._show_order_detail(item)

    def _on_delete(self, item: dict):
        status = item.get("status", "")
        if status not in ("cancelled", "pending"):
            QMessageBox.warning(self, "Hata",
                "Sadece 'Beklemede' veya 'İptal' durumundaki siparişler silinebilir.")
            return
        if self.confirm_delete(f"Sipariş #{item['ID']}"):
            order_id = item["ID"]
            for oi in self.order_item_repo.get_by_order(order_id):
                self.order_item_repo.delete(oi["ID"])
            for p in self.payment_repo.get_by_order(order_id):
                self.payment_repo.delete(p["ID"])
            self.controller.order_repo.delete(order_id)
            self.refresh_data()


    def _create_action_buttons(self, row: int, item: dict):
        actions_widget = QWidget()
        actions_widget.setStyleSheet("background: transparent;")
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(8, 4, 8, 4)
        actions_layout.setSpacing(8)

        if not self.edit_permission or has_permission(self.edit_permission):
            detail_btn = QPushButton("Detaylar")
            detail_btn.setCursor(Qt.PointingHandCursor)
            detail_btn.setFixedSize(80, 28)
            detail_btn.setStyleSheet(f"""
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
            detail_btn.clicked.connect(lambda checked, i=item: self._on_edit(i))
            actions_layout.addWidget(detail_btn)

        if not self.delete_permission or has_permission(self.delete_permission):
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
            del_btn.clicked.connect(lambda checked, i=item: self._on_delete(i))
            actions_layout.addWidget(del_btn)

        actions_layout.addStretch()
        self.table.setCellWidget(row, len(self.columns), actions_widget)


    def _render_table(self):
        super()._render_table()
        status_col = None
        for i, col in enumerate(self.columns):
            if col["key"] == "status":
                status_col = i
                break
        if status_col is not None:
            for row in range(self.table.rowCount()):
                cell = self.table.item(row, status_col)
                if cell:
                    for key, (label, color) in STATUS_MAP.items():
                        if cell.text() == label:
                            cell.setForeground(QColor(color))
                            break


class CreateOrderDialog(BaseDialog):
    def __init__(self, parent=None):
        self.edit_data = None
        self.controller = OrderController()
        self.customer_repo = CustomerRepository()
        self.product_repo = ProductRepository()
        self.variant_repo = VariantRepository()
        self.location_repo = LocationRepository()
        self.order_items = []

        super().__init__(parent, title="Yeni Sipariş Oluştur", width=750, height=650)

    def _setup_form(self):
        self.add_form_section_title("Müşteri")

        self.customer_combo = QComboBox()
        self.customer_combo.setStyleSheet(_input_style())
        self.customer_combo.addItem("Mağaza Müşterisi (Anonim)", 0)
        for c in self.customer_repo.get_active_customers():
            self.customer_combo.addItem(
                f"{c['first_name']} {c['last_name']} — {c.get('phone_number', '')}", c["ID"])
        _make_searchable(self.customer_combo)
        self.add_form_field("Müşteri", self.customer_combo)

        self.location_combo = QComboBox()
        self.location_combo.setStyleSheet(_input_style())
        self.location_combo.addItem("-- Otomatik (tüm lokasyonlardan düş) --", None)
        for loc in self.location_repo.get_all():
            self.location_combo.addItem(loc["name"], loc["ID"])
        _make_searchable(self.location_combo)
        self.add_form_field("Stok Lokasyonu", self.location_combo)

        self.add_form_separator()

        self.add_form_section_title("Ürün Ekle")

        scan_widget = QWidget()
        scan_widget.setStyleSheet("background: transparent;")
        scan_layout = QHBoxLayout(scan_widget)
        scan_layout.setContentsMargins(0, 0, 0, 0)
        scan_layout.setSpacing(8)

        self.scan_input = QLineEdit()
        self.scan_input.setPlaceholderText("🔍 Barkod veya SKU girin + Enter")
        self.scan_input.setFixedHeight(38)
        self.scan_input.setStyleSheet(_input_style())
        self.scan_input.returnPressed.connect(self._scan_barcode)
        scan_layout.addWidget(self.scan_input)

        scan_btn = QPushButton("Ekle")
        scan_btn.setCursor(Qt.PointingHandCursor)
        scan_btn.setFixedSize(70, 38)
        scan_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.SUCCESS};
                color: {Theme.TEXT_DARK};
                border: none; border-radius: 6px;
                font-weight: bold; font-size: 12px;
            }}
            QPushButton:hover {{ background-color: #5fddb5; }}
        """)
        scan_btn.clicked.connect(self._scan_barcode)
        scan_layout.addWidget(scan_btn)
        self.form_layout.addWidget(scan_widget)

        self.variant_combo = QComboBox()
        self.variant_combo.setStyleSheet(_input_style())
        self.variant_combo.addItem("-- veya listeden varyant seçin --", None)
        self._load_variants()
        _make_searchable(self.variant_combo)
        self.add_form_field("Varyant Seç", self.variant_combo)

        qty_price_widget = QWidget()
        qty_price_widget.setStyleSheet("background: transparent;")
        qp_layout = QHBoxLayout(qty_price_widget)
        qp_layout.setContentsMargins(0, 0, 0, 0)
        qp_layout.setSpacing(8)

        lbl_qty = QLabel("Adet:")
        lbl_qty.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        qp_layout.addWidget(lbl_qty)

        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 99999)
        self.qty_spin.setValue(1)
        self.qty_spin.setFixedWidth(80)
        self.qty_spin.setFixedHeight(34)
        self.qty_spin.setStyleSheet(_input_style())
        qp_layout.addWidget(self.qty_spin)

        lbl_price = QLabel("Birim Fiyat:")
        lbl_price.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        qp_layout.addWidget(lbl_price)

        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 9999999)
        self.price_spin.setDecimals(2)
        self.price_spin.setSuffix(" ₺")
        self.price_spin.setFixedWidth(130)
        self.price_spin.setFixedHeight(34)
        self.price_spin.setStyleSheet(_input_style())
        qp_layout.addWidget(self.price_spin)

        add_item_btn = QPushButton("+ Ekle")
        add_item_btn.setCursor(Qt.PointingHandCursor)
        add_item_btn.setFixedSize(80, 34)
        add_item_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT};
                color: white; border: none; border-radius: 6px;
                font-weight: bold; font-size: 12px;
            }}
            QPushButton:hover {{ background-color: #f05a73; }}
        """)
        add_item_btn.clicked.connect(self._add_item_from_combo)
        qp_layout.addWidget(add_item_btn)
        qp_layout.addStretch()
        self.form_layout.addWidget(qty_price_widget)

        self.add_form_separator()

        self.add_form_section_title("Sipariş Kalemleri")

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels(["Ürün", "SKU", "Adet", "Birim Fiyat", "Toplam", ""])
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for c in range(1, 5):
            self.items_table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
        self.items_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.items_table.horizontalHeader().resizeSection(5, 90)
        self.items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setFixedHeight(150)
        self.items_table.setStyleSheet(_table_style())
        self.form_layout.addWidget(self.items_table)

        discount_widget = QWidget()
        discount_widget.setStyleSheet("background: transparent;")
        discount_layout = QHBoxLayout(discount_widget)
        discount_layout.setContentsMargins(0, 0, 0, 0)
        discount_layout.setSpacing(8)

        discount_lbl = QLabel("İndirim:")
        discount_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 13px; background: transparent; font-weight: bold;")
        discount_layout.addWidget(discount_lbl)

        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setRange(0, 9999999)
        self.discount_spin.setDecimals(2)
        self.discount_spin.setSuffix(" ₺")
        self.discount_spin.setFixedWidth(150)
        self.discount_spin.setFixedHeight(34)
        self.discount_spin.setStyleSheet(_input_style())
        self.discount_spin.valueChanged.connect(self._update_totals)
        discount_layout.addWidget(self.discount_spin)
        discount_layout.addStretch()
        self.form_layout.addWidget(discount_widget)

        self.total_label = QLabel("Toplam: 0,00 ₺")
        self.total_label.setAlignment(Qt.AlignRight)
        self.total_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.total_label.setStyleSheet(f"color: {Theme.SUCCESS}; background: transparent;")
        self.form_layout.addWidget(self.total_label)

        self.add_form_separator()

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Sipariş notu (opsiyonel)")
        self.notes_input.setStyleSheet(_input_style())
        self.add_form_field("Not", self.notes_input)

    def _load_variants(self):
        for product in self.product_repo.get_active_products():
            for v in self.variant_repo.get_by_product(product["ID"]):
                label = f"{product['name']} — {v['sku']} (₺{v['sell_price']:,.2f})"
                self.variant_combo.addItem(label, v["ID"])

    def _scan_barcode(self):
        code = self.scan_input.text().strip()
        if not code:
            return

        variant = self.variant_repo.get_by_barcode(code)
        if not variant:
            variant = self.variant_repo.get_by_sku(code)

        if variant:
            product = self.product_repo.get_by_id(variant["product_ID"])
            product_name = product["name"] if product else "?"
            qty = self.qty_spin.value()
            price = self.price_spin.value() if self.price_spin.value() > 0 else variant["sell_price"]
            self._add_item(variant["ID"], product_name, variant["sku"], qty, price)
            self.scan_input.clear()
            self.scan_input.setPlaceholderText(f"✓ {product_name} — {qty} adet eklendi")
            self.scan_input.setStyleSheet(_input_style() + f"\nQLineEdit {{ border-color: {Theme.SUCCESS}; }}")
        else:
            self.scan_input.setStyleSheet(_input_style() + f"\nQLineEdit {{ border-color: {Theme.ERROR}; }}")
            self.scan_input.setPlaceholderText("✗ Ürün bulunamadı!")

    def _add_item_from_combo(self):
        variant_id = self.variant_combo.currentData()
        if not variant_id:
            return
        variant = self.variant_repo.get_by_id(variant_id)
        if not variant:
            return
        product = self.product_repo.get_by_id(variant["product_ID"])
        product_name = product["name"] if product else "?"
        qty = self.qty_spin.value()
        price = self.price_spin.value() if self.price_spin.value() > 0 else variant["sell_price"]
        self._add_item(variant_id, product_name, variant["sku"], qty, price)

    def _add_item(self, variant_id, product_name, sku, quantity, unit_price):
        for existing in self.order_items:
            if existing["variant_id"] == variant_id:
                existing["quantity"] += quantity
                self._refresh_items_table()
                return
        self.order_items.append({
            "variant_id": variant_id, "product_name": product_name,
            "sku": sku, "quantity": quantity, "unit_price": unit_price,
        })
        self._refresh_items_table()

    def _remove_item(self, index):
        if 0 <= index < len(self.order_items):
            item = self.order_items[index]
            if item["quantity"] > 1:
                qty, ok = QInputDialog.getInt(
                    self, "Adet Çıkar",
                    f"{item['product_name']} — Kaç adet çıkarmak istiyorsunuz?",
                    item["quantity"], 1, item["quantity"], 1
                )
                if not ok:
                    return
                if qty >= item["quantity"]:
                    self.order_items.pop(index)
                else:
                    item["quantity"] -= qty
            else:
                self.order_items.pop(index)
            self._refresh_items_table()

    def _refresh_items_table(self):
        self.items_table.setRowCount(len(self.order_items))
        for i, item in enumerate(self.order_items):
            line_total = item["quantity"] * item["unit_price"]
            self.items_table.setItem(i, 0, QTableWidgetItem(item["product_name"]))
            self.items_table.setItem(i, 1, QTableWidgetItem(item["sku"]))
            self.items_table.setItem(i, 2, QTableWidgetItem(str(item["quantity"])))
            self.items_table.setItem(i, 3, QTableWidgetItem(f"{item['unit_price']:,.2f} ₺"))
            self.items_table.setItem(i, 4, QTableWidgetItem(f"{line_total:,.2f} ₺"))

            btn_widget = QWidget()
            btn_widget.setStyleSheet("background: transparent;")
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(0)
            remove_btn = QPushButton("Çıkar")
            remove_btn.setCursor(Qt.PointingHandCursor)
            remove_btn.setFixedSize(70, 28)
            remove_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.ERROR};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0 8px;
                }}
                QPushButton:hover {{ background-color: #ff8a8a; }}
            """)
            remove_btn.clicked.connect(lambda checked, idx=i: self._remove_item(idx))
            btn_layout.addWidget(remove_btn)
            self.items_table.setCellWidget(i, 5, btn_widget)
            self.items_table.setRowHeight(i, 36)
        self._update_totals()

    def _update_totals(self):
        subtotal = sum(it["quantity"] * it["unit_price"] for it in self.order_items)
        discount = self.discount_spin.value()
        net = subtotal - discount
        if discount > 0:
            self.total_label.setText(
                f"Ara Toplam: {subtotal:,.2f} ₺  —  İndirim: {discount:,.2f} ₺  —  Net: {net:,.2f} ₺")
        else:
            self.total_label.setText(f"Toplam: {subtotal:,.2f} ₺")

    def _on_save(self):
        if not self.order_items:
            self.show_error("Sipariş en az bir ürün içermelidir!")
            return

        items = [{"variant_id": it["variant_id"], "quantity": it["quantity"],
                   "unit_price": it["unit_price"]} for it in self.order_items]

        result = self.controller.create_order(
            items=items,
            customer_id=self.customer_combo.currentData() or 0,
            location_id=self.location_combo.currentData(),
            notes=self.notes_input.text().strip(),
            discount_price=self.discount_spin.value()
        )

        if result["success"]:
            self.result_data = {"order_id": result["order_id"]}
            self.accept()
        else:
            self.show_error(result["message"])

    def _input_style(self):
        return _input_style()


class AddPaymentDialog(BaseDialog):
    def __init__(self, parent=None, order: dict = None):
        self.order = order
        self.edit_data = None
        self.order_item_repo = OrderItemRepository()
        self.payment_repo = PaymentRepository()

        order_id = order["ID"] if order else "?"
        super().__init__(parent, title=f"Ödeme Ekle — Sipariş #{order_id}", width=420, height=380)

    def _setup_form(self):
        self._remaining = 0.0
        if self.order:
            order_total = self.order_item_repo.get_order_total(self.order["ID"])
            paid_total = self.payment_repo.get_order_paid_total(self.order["ID"])
            discount = self.order.get("discount_price", 0.0) or 0.0
            net_total = order_total - discount
            self._remaining = net_total - paid_total

            info_label = QLabel(
                f"Sipariş Tutarı: {order_total:,.2f} ₺\n"
                f"İndirim: {discount:,.2f} ₺\n"
                f"Net Tutar: {net_total:,.2f} ₺\n"
                f"Ödenen: {paid_total:,.2f} ₺\n"
                f"Kalan: {self._remaining:,.2f} ₺"
            )
            info_label.setStyleSheet(f"""
                color: {Theme.TEXT_SECONDARY};
                background-color: {Theme.BG_CARD};
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
            """)
            self.form_layout.addWidget(info_label)
            self.add_form_separator()

            if self._remaining <= 0:
                warn_label = QLabel("✓ Bu siparişin ödemesi tamamlanmış.")
                warn_label.setStyleSheet(f"""
                    color: {Theme.SUCCESS};
                    background-color: {Theme.BG_CARD};
                    border-radius: 8px;
                    padding: 12px;
                    font-size: 14px;
                    font-weight: bold;
                """)
                self.form_layout.addWidget(warn_label)
                self.save_btn.setEnabled(False)
                self.save_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {Theme.TEXT_MUTED};
                        color: {Theme.BG_DARK};
                        border: none; border-radius: 8px;
                        font-size: 13px; font-weight: bold;
                    }}
                """)
                return

        self.add_form_section_title("Ödeme Bilgileri")

        self.method_combo = QComboBox()
        self.method_combo.setStyleSheet(_input_style())
        for key, label in PAYMENT_METHOD_MAP.items():
            self.method_combo.addItem(label, key)
        self.add_form_field("Ödeme Yöntemi", self.method_combo, required=True)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, max(self._remaining, 0.01))
        self.amount_spin.setDecimals(2)
        self.amount_spin.setSuffix(" ₺")
        self.amount_spin.setStyleSheet(_input_style())
        self.amount_spin.setValue(max(self._remaining, 0.01))
        self.add_form_field("Tutar", self.amount_spin, required=True)

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Ödeme notu (opsiyonel)")
        self.note_input.setStyleSheet(_input_style())
        self.add_form_field("Not", self.note_input)
        self.form_layout.addStretch()

    def _on_save(self):
        amount = self.amount_spin.value()
        if amount <= 0:
            self.show_error("Tutar 0'dan büyük olmalıdır!")
            return
        self.result_data = {
            "method": self.method_combo.currentData(),
            "amount": amount,
            "note": self.note_input.text().strip(),
        }
        self.accept()

    def _input_style(self):
        return _input_style()


class OrderDetailDialog(QDialog):
    def __init__(self, parent=None, order_id: int = None):
        super().__init__(parent)
        self.order_controller = OrderController()
        self.customer_repo = CustomerRepository()
        self.variant_repo = VariantRepository()
        self.order_item_repo = OrderItemRepository()
        self.payment_repo = PaymentRepository()
        self.order_id = order_id

        self.setWindowTitle(f"Sipariş Detay — #{order_id}")
        self.setFixedSize(700, 620)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag_pos = None
        self._setup_ui()

    def _setup_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame()
        container.setObjectName("detailContainer")
        container.setStyleSheet(f"""
            QFrame#detailContainer {{
                background-color: {Theme.BG_DARK};
                border-radius: 12px;
                border: 1px solid {Theme.BORDER};
            }}
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

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
        header_layout.setContentsMargins(20, 0, 10, 0)

        title_label = QLabel(f"📋 Sipariş Detay — #{self.order_id}")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; background: transparent;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {Theme.TEXT_SECONDARY};
                border: none; font-size: 16px; border-radius: 16px; }}
            QPushButton:hover {{ background-color: {Theme.ERROR}; color: white; }}
        """)
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)
        container_layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background-color: {Theme.BG_DARK}; }}")
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(20, 15, 20, 15)
        self.content_layout.setSpacing(12)
        scroll.setWidget(content)
        container_layout.addWidget(scroll)

        footer = QFrame()
        footer.setFixedHeight(50)
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SIDEBAR};
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
                border-top: 1px solid {Theme.BORDER};
            }}
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 0, 20, 0)
        footer_layout.addStretch()
        close_btn2 = QPushButton("Kapat")
        close_btn2.setCursor(Qt.PointingHandCursor)
        close_btn2.setFixedSize(100, 36)
        close_btn2.setStyleSheet(Theme.get_outline_button_style())
        close_btn2.clicked.connect(self.reject)
        footer_layout.addWidget(close_btn2)
        container_layout.addWidget(footer)

        outer_layout.addWidget(container)
        self._load_data()

    def _load_data(self):
        result = self.order_controller.get_order(self.order_id)
        if not result["success"]:
            return
        order = result["data"]

        self._add_section_title("Sipariş Bilgileri")
        info_frame = self._card_frame()
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(6)

        customer_name = "Mağaza Müşterisi"
        if order.get("customer_ID") and order["customer_ID"] > 0:
            c = self.customer_repo.get_by_id(order["customer_ID"])
            if c:
                customer_name = f"{c['first_name']} {c['last_name']}"

        status_label, status_color = STATUS_MAP.get(order.get("status", "pending"), ("?", Theme.TEXT_MUTED))

        rows = [
            ("Müşteri", customer_name, None),
            ("Durum", status_label, status_color),
            ("Tarih", order.get("created_at", "-")[:16] if order.get("created_at") else "-", None),
            ("Not", order.get("notes", "") or "—", None),
        ]
        if order.get("status") == "cancelled":
            rows.append(("İptal Nedeni", order.get("cancellation_reason", "—"), Theme.ERROR))
            rows.append(("İptal Tarihi", (order.get("cancellation_date", "") or "—")[:16], None))

        for label, value, color in rows:
            self._add_info_row(info_layout, label, str(value), color)
        self.content_layout.addWidget(info_frame)

        self._add_section_title("Sipariş Kalemleri")
        items = order.get("items", [])
        items_table = QTableWidget()
        items_table.setColumnCount(5)
        items_table.setHorizontalHeaderLabels(["Ürün", "SKU", "Adet", "Birim Fiyat", "Toplam"])
        items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for c in range(1, 5):
            items_table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
        items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        items_table.verticalHeader().setVisible(False)
        items_table.setRowCount(len(items))
        items_table.setFixedHeight(min(40 + len(items) * 32, 200))
        items_table.setStyleSheet(_table_style())

        for i, it in enumerate(items):
            line_total = it["quantity"] * it["unit_price"]
            items_table.setItem(i, 0, QTableWidgetItem(it.get("product_name", "?")))
            v = self.variant_repo.get_by_id(it.get("variant_ID"))
            items_table.setItem(i, 1, QTableWidgetItem(v["sku"] if v else "—"))
            items_table.setItem(i, 2, QTableWidgetItem(str(it["quantity"])))
            items_table.setItem(i, 3, QTableWidgetItem(f"{it['unit_price']:,.2f} ₺"))
            items_table.setItem(i, 4, QTableWidgetItem(f"{line_total:,.2f} ₺"))
        self.content_layout.addWidget(items_table)

        self._add_section_title("Ödeme Bilgileri")
        ps_result = self.order_controller.get_order_payment_summary(self.order_id)
        if ps_result["success"]:
            ps = ps_result["data"]
            summary_frame = self._card_frame()
            summary_layout = QVBoxLayout(summary_frame)
            summary_layout.setSpacing(4)

            remaining = ps['remaining']
            max_refundable = ps.get('max_refundable', ps['net_total'] - ps['refund_total'])
            finance_rows = [
                ("Sipariş Tutarı", f"{ps['order_total']:,.2f} ₺", Theme.TEXT_PRIMARY),
                ("İndirim", f"-{ps['discount']:,.2f} ₺", Theme.WARNING),
                ("Net Tutar", f"{ps['net_total']:,.2f} ₺", Theme.TEXT_PRIMARY),
                ("Ödenen", f"{ps['paid_total']:,.2f} ₺", Theme.SUCCESS),
                ("Kalan Borç", f"{remaining:,.2f} ₺",
                 Theme.ERROR if remaining > 0 else Theme.SUCCESS),
                ("İade Edilen", f"{ps['refund_total']:,.2f} ₺", Theme.ERROR if ps['refund_total'] > 0 else Theme.TEXT_MUTED),
                ("İade Edilebilir", f"{max_refundable:,.2f} ₺",
                 Theme.WARNING if max_refundable > 0 else Theme.TEXT_MUTED),
            ]
            for label, value, color in finance_rows:
                self._add_info_row(summary_layout, label, value, color, bold_value=True)
            self.content_layout.addWidget(summary_frame)

            payments = ps.get("payments", [])
            if payments:
                pay_table = QTableWidget()
                pay_table.setColumnCount(4)
                pay_table.setHorizontalHeaderLabels(["Yöntem", "Tutar", "Tarih", "Not"])
                pay_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
                for c in range(3):
                    pay_table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
                pay_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
                pay_table.verticalHeader().setVisible(False)
                pay_table.setRowCount(len(payments))
                pay_table.setFixedHeight(min(40 + len(payments) * 32, 150))
                pay_table.setStyleSheet(_table_style())
                for i, p in enumerate(payments):
                    pay_table.setItem(i, 0, QTableWidgetItem(
                        PAYMENT_METHOD_MAP.get(p.get("method", ""), p.get("method", ""))))
                    pay_table.setItem(i, 1, QTableWidgetItem(f"{p['amount']:,.2f} ₺"))
                    pay_table.setItem(i, 2, QTableWidgetItem(
                        p.get("payment_date", "")[:16] if p.get("payment_date") else "—"))
                    pay_table.setItem(i, 3, QTableWidgetItem(p.get("note", "") or "—"))
                self.content_layout.addWidget(pay_table)

        refund_history = order.get("refund_history", [])
        if refund_history and isinstance(refund_history, list) and len(refund_history) > 0:
            self._add_section_title("İade Geçmişi")
            for entry in refund_history:
                rf_frame = self._card_frame()
                rf_layout = QVBoxLayout(rf_frame)
                rf_layout.setSpacing(3)
                self._add_info_row(rf_layout, "Tarih", entry.get("date", "—")[:16], None)
                self._add_info_row(rf_layout, "Tutar", f"{entry.get('amount', 0):,.2f} ₺", Theme.ERROR)
                self._add_info_row(rf_layout, "Neden", entry.get("reason", "—"), None)
                self._add_info_row(rf_layout, "İşlemi Yapan", entry.get("user", "—"), None)
                items_text = ""
                for ri in entry.get("items", []):
                    items_text += f"Varyant #{ri.get('variant_id', '?')} x{ri.get('quantity', 0)}, "
                if items_text:
                    self._add_info_row(rf_layout, "Ürünler", items_text.rstrip(", "), None)
                self.content_layout.addWidget(rf_frame)

        self.content_layout.addStretch()

    def _card_frame(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        return frame

    def _add_section_title(self, title):
        lbl = QLabel(title)
        lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        lbl.setStyleSheet(f"color: {Theme.ACCENT}; background: transparent;")
        self.content_layout.addWidget(lbl)

    def _add_info_row(self, layout, label, value, color=None, bold_value=False):
        row = QHBoxLayout()
        lbl = QLabel(f"{label}:")
        lbl.setFixedWidth(110)
        lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 12px; background: transparent; font-weight: bold;")
        val = QLabel(str(value))
        style = f"font-size: 12px; background: transparent;"
        if color:
            style += f" color: {color};"
        else:
            style += f" color: {Theme.TEXT_PRIMARY};"
        if bold_value:
            style += " font-weight: bold;"
        val.setStyleSheet(style)
        val.setWordWrap(True)
        row.addWidget(lbl)
        row.addWidget(val)
        row.addStretch()
        layout.addLayout(row)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.pos().y() < 50:
            self._drag_pos = event.globalPos() - self.pos()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


class EditOrderItemsDialog(QDialog):
    def __init__(self, parent=None, order_id: int = None):
        super().__init__(parent)
        self.order_id = order_id
        self.controller = OrderController()
        self.product_repo = ProductRepository()
        self.variant_repo = VariantRepository()
        self.location_repo = LocationRepository()
        self.order_item_repo = OrderItemRepository()

        self.setWindowTitle(f"Kalemleri Düzenle — #{order_id}")
        self.setFixedSize(720, 580)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag_pos = None
        self._setup_ui()

    def _setup_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame()
        container.setObjectName("editContainer")
        container.setStyleSheet(f"""
            QFrame#editContainer {{
                background-color: {Theme.BG_DARK};
                border-radius: 12px;
                border: 1px solid {Theme.BORDER};
            }}
        """)
        clayout = QVBoxLayout(container)
        clayout.setContentsMargins(0, 0, 0, 0)
        clayout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SIDEBAR};
                border-top-left-radius: 12px; border-top-right-radius: 12px;
                border-bottom: 1px solid {Theme.BORDER};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 10, 0)
        title_lbl = QLabel(f"📝 Kalemleri Düzenle — Sipariş #{self.order_id}")
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; background: transparent;")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {Theme.TEXT_SECONDARY};
                border: none; font-size: 16px; border-radius: 16px; }}
            QPushButton:hover {{ background-color: {Theme.ERROR}; color: white; }}
        """)
        close_btn.clicked.connect(self.accept)
        header_layout.addWidget(close_btn)
        clayout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background-color: {Theme.BG_DARK}; }}")
        content = QWidget()
        form = QVBoxLayout(content)
        form.setContentsMargins(20, 15, 20, 15)
        form.setSpacing(12)

        loc_lbl = QLabel("Stok Lokasyonu (ekleme için)")
        loc_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; font-weight: bold; background: transparent;")
        form.addWidget(loc_lbl)

        self.location_combo = QComboBox()
        self.location_combo.setFixedHeight(38)
        self.location_combo.setStyleSheet(_input_style())
        self.location_combo.addItem("-- Otomatik (tüm lokasyonlardan) --", None)
        for loc in self.location_repo.get_all():
            self.location_combo.addItem(loc["name"], loc["ID"])
        _make_searchable(self.location_combo)
        form.addWidget(self.location_combo)

        sep1 = QFrame()
        sep1.setFixedHeight(1)
        sep1.setStyleSheet(f"background-color: {Theme.BORDER};")
        form.addWidget(sep1)

        add_title = QLabel("Ürün Ekle")
        add_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        add_title.setStyleSheet(f"color: {Theme.ACCENT}; background: transparent;")
        form.addWidget(add_title)

        scan_w = QWidget()
        scan_w.setStyleSheet("background: transparent;")
        scan_l = QHBoxLayout(scan_w)
        scan_l.setContentsMargins(0, 0, 0, 0)
        scan_l.setSpacing(8)

        self.scan_input = QLineEdit()
        self.scan_input.setPlaceholderText("🔍 Barkod veya SKU girin + Enter")
        self.scan_input.setFixedHeight(38)
        self.scan_input.setStyleSheet(_input_style())
        self.scan_input.returnPressed.connect(self._scan_and_add)
        scan_l.addWidget(self.scan_input)

        scan_btn = QPushButton("Ekle")
        scan_btn.setCursor(Qt.PointingHandCursor)
        scan_btn.setFixedSize(70, 38)
        scan_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.SUCCESS}; color: {Theme.TEXT_DARK};
                border: none; border-radius: 6px; font-weight: bold; font-size: 12px; }}
            QPushButton:hover {{ background-color: #5fddb5; }}
        """)
        scan_btn.clicked.connect(self._scan_and_add)
        scan_l.addWidget(scan_btn)
        form.addWidget(scan_w)

        qp_w = QWidget()
        qp_w.setStyleSheet("background: transparent;")
        qp_l = QHBoxLayout(qp_w)
        qp_l.setContentsMargins(0, 0, 0, 0)
        qp_l.setSpacing(8)

        qp_l.addWidget(QLabel("Adet:"))
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 99999)
        self.qty_spin.setValue(1)
        self.qty_spin.setFixedWidth(80)
        self.qty_spin.setFixedHeight(34)
        self.qty_spin.setStyleSheet(_input_style())
        qp_l.addWidget(self.qty_spin)

        qp_l.addWidget(QLabel("Fiyat:"))
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 9999999)
        self.price_spin.setDecimals(2)
        self.price_spin.setSuffix(" ₺")
        self.price_spin.setFixedWidth(130)
        self.price_spin.setFixedHeight(34)
        self.price_spin.setStyleSheet(_input_style())
        qp_l.addWidget(self.price_spin)
        qp_l.addStretch()

        for w in qp_w.findChildren(QLabel):
            w.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        form.addWidget(qp_w)

        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background-color: {Theme.BORDER};")
        form.addWidget(sep2)

        items_title = QLabel("Mevcut Kalemler")
        items_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        items_title.setStyleSheet(f"color: {Theme.ACCENT}; background: transparent;")
        form.addWidget(items_title)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(["Ürün", "SKU", "Adet", "Birim Fiyat", "Toplam"])
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for c in range(1, 5):
            self.items_table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
        self.items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setFixedHeight(180)
        self.items_table.setStyleSheet(_table_style())
        form.addWidget(self.items_table)

        info_note = QLabel("ℹ️ Ürün çıkarmak için sağ tık menüsünden 'İade İşlemi' kullanın.")
        info_note.setStyleSheet(f"""
            color: {Theme.INFO};
            background-color: transparent;
            font-size: 11px;
            font-style: italic;
            padding: 4px 0;
        """)
        form.addWidget(info_note)

        self.total_label = QLabel("")
        self.total_label.setAlignment(Qt.AlignRight)
        self.total_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.total_label.setStyleSheet(f"color: {Theme.SUCCESS}; background: transparent;")
        form.addWidget(self.total_label)

        scroll.setWidget(content)
        clayout.addWidget(scroll)

        footer = QFrame()
        footer.setFixedHeight(50)
        footer.setStyleSheet(f"""
            QFrame {{ background-color: {Theme.BG_SIDEBAR};
                border-bottom-left-radius: 12px; border-bottom-right-radius: 12px;
                border-top: 1px solid {Theme.BORDER}; }}
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 0, 20, 0)
        footer_layout.addStretch()
        close_btn2 = QPushButton("Kapat")
        close_btn2.setCursor(Qt.PointingHandCursor)
        close_btn2.setFixedSize(100, 36)
        close_btn2.setStyleSheet(Theme.get_outline_button_style())
        close_btn2.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn2)
        clayout.addWidget(footer)

        outer_layout.addWidget(container)
        self._refresh_items()

    def _scan_and_add(self):
        code = self.scan_input.text().strip()
        if not code:
            return

        variant = self.variant_repo.get_by_barcode(code)
        if not variant:
            variant = self.variant_repo.get_by_sku(code)

        if not variant:
            self.scan_input.setStyleSheet(_input_style() + f"\nQLineEdit {{ border-color: {Theme.ERROR}; }}")
            return

        product = self.product_repo.get_by_id(variant["product_ID"])
        qty = self.qty_spin.value()
        price = self.price_spin.value() if self.price_spin.value() > 0 else variant["sell_price"]

        result = self.controller.add_order_item(
            order_id=self.order_id, variant_id=variant["ID"],
            quantity=qty, unit_price=price,
            location_id=self.location_combo.currentData()
        )
        if result["success"]:
            self.scan_input.clear()
            self.scan_input.setStyleSheet(_input_style() + f"\nQLineEdit {{ border-color: {Theme.SUCCESS}; }}")
            p_name = product["name"] if product else "?"
            self.scan_input.setPlaceholderText(f"✓ {p_name} — {qty} adet eklendi")
            self._refresh_items()
        else:
            QMessageBox.warning(self, "Hata", result["message"])

    def _refresh_items(self):
        items = self.order_item_repo.get_by_order(self.order_id)
        self.items_table.setRowCount(len(items))
        total = 0.0

        for i, it in enumerate(items):
            line_total = it["quantity"] * it["unit_price"]
            total += line_total
            v = self.variant_repo.get_by_id(it["variant_ID"])

            self.items_table.setItem(i, 0, QTableWidgetItem(it.get("product_name", "?")))
            self.items_table.setItem(i, 1, QTableWidgetItem(v["sku"] if v else "—"))
            self.items_table.setItem(i, 2, QTableWidgetItem(str(it["quantity"])))
            self.items_table.setItem(i, 3, QTableWidgetItem(f"{it['unit_price']:,.2f} ₺"))
            self.items_table.setItem(i, 4, QTableWidgetItem(f"{line_total:,.2f} ₺"))
            self.items_table.setRowHeight(i, 36)

        self.total_label.setText(f"Toplam: {total:,.2f} ₺")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.pos().y() < 50:
            self._drag_pos = event.globalPos() - self.pos()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


class RefundDialog(BaseDialog):
    def __init__(self, parent=None, order_id: int = None):
        self.order_id = order_id
        self.edit_data = None
        self.controller = OrderController()
        self.order_item_repo = OrderItemRepository()
        self.variant_repo = VariantRepository()
        self.location_repo = LocationRepository()
        self.payment_repo = PaymentRepository()
        self.refund_rows = []

        super().__init__(parent, title=f"İade İşlemi — Sipariş #{order_id}", width=580, height=560)
        self.save_btn.setText("↩️ İade Yap")

    def _setup_form(self):
        order_total = self.order_item_repo.get_order_total(self.order_id)
        order = self.controller.order_repo.get_by_id(self.order_id)
        previous_refund = order.get("refund_price", 0.0) or 0.0 if order else 0.0
        discount = order.get("discount_price", 0.0) or 0.0 if order else 0.0
        net_total = order_total - discount
        self._max_refundable = net_total - previous_refund
        self._discount_ratio = (net_total / order_total) if order_total > 0 else 1.0

        info_label = QLabel(
            f"Sipariş Tutarı: {order_total:,.2f} ₺\n"
            f"İndirim: {discount:,.2f} ₺\n"
            f"Net Tutar: {net_total:,.2f} ₺\n"
            f"Önceki İadeler: {previous_refund:,.2f} ₺\n"
            f"İade Edilebilir: {self._max_refundable:,.2f} ₺"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"""
            color: {Theme.TEXT_SECONDARY};
            background-color: {Theme.BG_CARD};
            border-radius: 8px; padding: 12px; font-size: 12px;
        """)
        self.form_layout.addWidget(info_label)

        if self._max_refundable <= 0:
            warn_label = QLabel("✓ Bu siparişin tamamı zaten iade edilmiş.")
            warn_label.setStyleSheet(f"""
                color: {Theme.ERROR};
                background-color: {Theme.BG_CARD};
                border-radius: 8px; padding: 12px;
                font-size: 14px; font-weight: bold;
            """)
            self.form_layout.addWidget(warn_label)
            self.save_btn.setEnabled(False)
            self.save_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.TEXT_MUTED};
                    color: {Theme.BG_DARK};
                    border: none; border-radius: 8px;
                    font-size: 13px; font-weight: bold;
                }}
            """)
            return

        self.add_form_separator()
        self.add_form_section_title("İade Edilecek Ürünler")

        btn_widget = QWidget()
        btn_widget.setStyleSheet("background: transparent;")
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)

        select_all_btn = QPushButton("Tümünü Seç")
        select_all_btn.setCursor(Qt.PointingHandCursor)
        select_all_btn.setFixedHeight(30)
        select_all_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.INFO}; color: white;
                border: none; border-radius: 5px; padding: 0 12px; font-size: 11px; font-weight: bold; }}
            QPushButton:hover {{ background-color: #5bc7e0; }}
        """)
        select_all_btn.clicked.connect(self._select_all)
        btn_layout.addWidget(select_all_btn)

        clear_btn = QPushButton("Temizle")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setFixedHeight(30)
        clear_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.BG_HOVER}; color: {Theme.TEXT_SECONDARY};
                border: none; border-radius: 5px; padding: 0 12px; font-size: 11px; }}
            QPushButton:hover {{ background-color: {Theme.BORDER}; }}
        """)
        clear_btn.clicked.connect(self._clear_all)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        self.form_layout.addWidget(btn_widget)

        items = self.order_item_repo.get_by_order(self.order_id)
        for it in items:
            v = self.variant_repo.get_by_id(it["variant_ID"])
            sku = v["sku"] if v else "?"

            row_widget = QWidget()
            row_widget.setStyleSheet(f"""
                QWidget {{
                    background-color: {Theme.BG_CARD};
                    border-radius: 6px;
                    padding: 6px;
                }}
            """)
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(8, 4, 8, 4)
            row_layout.setSpacing(10)

            cb = QCheckBox()
            cb.setStyleSheet(f"""
                QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 4px;
                    border: 2px solid {Theme.BORDER}; background-color: {Theme.BG_INPUT}; }}
                QCheckBox::indicator:checked {{
                    background-color: {Theme.SUCCESS}; border-color: {Theme.SUCCESS}; }}
            """)
            row_layout.addWidget(cb)

            name_lbl = QLabel(f"{it.get('product_name', '?')} — {sku}")
            name_lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 12px; background: transparent;")
            name_lbl.setMinimumWidth(200)
            row_layout.addWidget(name_lbl)

            qty_spin = QSpinBox()
            qty_spin.setRange(0, it["quantity"])
            qty_spin.setValue(it["quantity"])
            qty_spin.setFixedWidth(70)
            qty_spin.setFixedHeight(30)
            qty_spin.setStyleSheet(_input_style())
            qty_spin.setEnabled(False)
            row_layout.addWidget(qty_spin)

            max_lbl = QLabel(f"/ {it['quantity']}")
            max_lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px; background: transparent;")
            row_layout.addWidget(max_lbl)

            price_lbl = QLabel(f"× {it['unit_price']:,.2f} ₺")
            price_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
            row_layout.addWidget(price_lbl)

            row_layout.addStretch()

            cb.stateChanged.connect(lambda state, qs=qty_spin: qs.setEnabled(state == Qt.Checked))
            cb.stateChanged.connect(lambda: self._update_refund_total())
            qty_spin.valueChanged.connect(lambda: self._update_refund_total())

            self.refund_rows.append({
                "checkbox": cb, "qty_spin": qty_spin,
                "max_qty": it["quantity"], "unit_price": it["unit_price"],
                "variant_id": it["variant_ID"], "item_id": it["ID"],
            })
            self.form_layout.addWidget(row_widget)

        self.refund_total_label = QLabel("İade Tutarı: 0,00 ₺")
        self.refund_total_label.setAlignment(Qt.AlignRight)
        self.refund_total_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.refund_total_label.setStyleSheet(f"color: {Theme.ERROR}; background: transparent;")
        self.form_layout.addWidget(self.refund_total_label)

        self.add_form_separator()

        self.refund_location_combo = QComboBox()
        self.refund_location_combo.setStyleSheet(_input_style())
        self.refund_location_combo.addItem("-- Stok iade lokasyonu seçin --", None)
        for loc in self.location_repo.get_all():
            self.refund_location_combo.addItem(loc["name"], loc["ID"])
        _make_searchable(self.refund_location_combo)
        self.add_form_field("Stok İade Lokasyonu", self.refund_location_combo)

        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("İade nedeni girin")
        self.reason_input.setStyleSheet(_input_style())
        self.add_form_field("İade Nedeni", self.reason_input, required=True)

    def _select_all(self):
        for row in self.refund_rows:
            row["checkbox"].setChecked(True)
            row["qty_spin"].setValue(row["max_qty"])

    def _clear_all(self):
        for row in self.refund_rows:
            row["checkbox"].setChecked(False)
            row["qty_spin"].setValue(0)

    def _update_refund_total(self):
        gross = 0.0
        for row in self.refund_rows:
            if row["checkbox"].isChecked():
                gross += row["qty_spin"].value() * row["unit_price"]
        net = gross * self._discount_ratio
        if abs(gross - net) > 0.01:
            self.refund_total_label.setText(
                f"Brüt: {gross:,.2f} ₺  →  İndirimli İade: {net:,.2f} ₺")
        else:
            self.refund_total_label.setText(f"İade Tutarı: {net:,.2f} ₺")

    def _on_save(self):
        selected = []
        gross_amount = 0.0
        for row in self.refund_rows:
            if row["checkbox"].isChecked() and row["qty_spin"].value() > 0:
                qty = row["qty_spin"].value()
                selected.append({"variant_id": row["variant_id"], "quantity": qty})
                gross_amount += qty * row["unit_price"]

        if not selected:
            self.show_error("En az bir ürün seçmelisiniz!")
            return

        refund_amount = round(gross_amount * self._discount_ratio, 2)

        if refund_amount > self._max_refundable:
            self.show_error(
                f"İade tutarı ({refund_amount:,.2f} ₺), iade edilebilir tutarı "
                f"({self._max_refundable:,.2f} ₺) aşıyor!")
            return

        reason = self.reason_input.text().strip()
        if not reason:
            self.show_error("İade nedeni boş bırakılamaz!")
            return

        location_id = self.refund_location_combo.currentData()

        result = self.controller.refund_order(
            order_id=self.order_id,
            refund_price=refund_amount,
            reason=reason,
            location_id=location_id,
            refund_items=selected
        )

        if result["success"]:
            QMessageBox.information(self, "Başarılı", result["message"])
            self.result_data = {"refund": refund_amount}
            self.accept()
        else:
            self.show_error(result["message"])

    def _input_style(self):
        return _input_style()


class DiscountDialog(BaseDialog):
    def __init__(self, parent=None, order: dict = None):
        self.order = order
        self.edit_data = None
        self.order_item_repo = OrderItemRepository()

        order_id = order["ID"] if order else "?"
        super().__init__(parent, title=f"İndirim Uygula — Sipariş #{order_id}", width=420, height=300)
        self.save_btn.setText("🏷️ Uygula")

    def _setup_form(self):
        if self.order:
            order_total = self.order_item_repo.get_order_total(self.order["ID"])
            current_discount = self.order.get("discount_price", 0.0) or 0.0
            net = order_total - current_discount

            info_label = QLabel(
                f"Sipariş Tutarı: {order_total:,.2f} ₺\n"
                f"Mevcut İndirim: {current_discount:,.2f} ₺\n"
                f"Net Tutar: {net:,.2f} ₺"
            )
            info_label.setStyleSheet(f"""
                color: {Theme.TEXT_SECONDARY};
                background-color: {Theme.BG_CARD};
                border-radius: 8px; padding: 12px; font-size: 13px;
            """)
            self.form_layout.addWidget(info_label)
            self.add_form_separator()

        self.add_form_section_title("İndirim Tutarı")

        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setRange(0, 9999999)
        self.discount_spin.setDecimals(2)
        self.discount_spin.setSuffix(" ₺")
        self.discount_spin.setStyleSheet(_input_style())
        if self.order:
            self.discount_spin.setValue(self.order.get("discount_price", 0.0) or 0.0)
        self.add_form_field("İndirim (₺)", self.discount_spin, required=True)

        self.form_layout.addStretch()

    def _on_save(self):
        self.result_data = {"discount": self.discount_spin.value()}
        self.accept()

    def _input_style(self):
        return _input_style()
