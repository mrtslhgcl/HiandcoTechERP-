import math

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFrame,
    QComboBox, QTabWidget, QSpinBox, QFormLayout, QTextEdit, QSizePolicy,
    QMenu, QAction, QAbstractItemView, QCompleter
)
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QStringListModel
from PyQt5.QtGui import QFont
from controllers.stock_controller import StockController
from controllers.product_controller import ProductController
from controllers.location_controller import LocationController
from utils.theme import Theme


class StockView(QWidget):
    def __init__(self):
        super().__init__()
        self.stock_controller = StockController()
        self.product_controller = ProductController()
        self.location_controller = LocationController()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("📊 Stok Yönetimi")
        title.setFont(QFont(Theme.FONT_FAMILY, Theme.FONT_SIZE_TITLE, QFont.Bold))
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        layout.addWidget(title)

        self.summary_layout = QHBoxLayout()
        self.summary_layout.setSpacing(15)
        layout.addLayout(self.summary_layout)
        self._build_summary_cards()

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
                min-width: 130px;   
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

        self.tabs.addTab(self._build_stock_overview_tab(), "📦 Stok Durumu")
        self.tabs.addTab(self._build_stock_in_tab(), "➕ Stok Giriş")
        self.tabs.addTab(self._build_stock_out_tab(), "➖ Stok Çıkış")
        self.tabs.addTab(self._build_transfer_tab(), "🔄 Transfer")
        self.tabs.addTab(self._build_adjustment_tab(), "📋 Sayım")
        self.tabs.addTab(self._build_movements_tab(), "📜 Hareket Geçmişi")

        layout.addWidget(self.tabs)


    def _build_summary_cards(self):
        while self.summary_layout.count():
            child = self.summary_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        products = self.product_controller.get_all_products()
        product_count = len(products["data"]) if products["success"] else 0

        all_variants = self.stock_controller.variant_repo.get_all()
        total_stock = 0
        low_stock_count = 0
        location_set = set()

        for v in all_variants:
            import json
            quantities = json.loads(v.get("location_quantities", "{}"))
            variant_total = sum(quantities.values())
            total_stock += variant_total
            if 0 < variant_total <= 10:
                low_stock_count += 1
            for loc_id in quantities.keys():
                location_set.add(loc_id)

        cards = [
            ("📦 Toplam Ürün", str(product_count), Theme.INFO),
            ("📊 Toplam Stok", str(total_stock), Theme.SUCCESS),
            ("⚠️ Düşük Stok", str(low_stock_count), Theme.WARNING),
            ("📍 Aktif Lokasyon", str(len(location_set)), Theme.ACCENT),
        ]

        for title, value, color in cards:
            card = self._create_summary_card(title, value, color)
            self.summary_layout.addWidget(card)

    def _create_summary_card(self, title: str, value: str, color: str) -> QFrame:
        card = QFrame()
        card.setFixedHeight(90)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border-radius: {Theme.BORDER_RADIUS}px;
                border-left: 4px solid {color};
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 10, 15, 10)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px;")
        card_layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setFont(QFont(Theme.FONT_FAMILY, 22, QFont.Bold))
        value_label.setStyleSheet(f"color: {color};")
        card_layout.addWidget(value_label)

        return card


    def _build_stock_overview_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        filter_layout = QHBoxLayout()

        search_label = QLabel("🔍 Ara:")
        search_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        self.overview_search = QLineEdit()
        self.overview_search.setPlaceholderText("SKU, barkod veya ürün adı...")
        self.overview_search.setStyleSheet(self._input_style())
        self.overview_search.textChanged.connect(self._filter_stock_overview)
        filter_layout.addWidget(search_label)
        filter_layout.addWidget(self.overview_search)

        loc_label = QLabel("Lokasyon:")
        loc_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        self.overview_location_combo = QComboBox()
        self.overview_location_combo.setStyleSheet(self._combo_style())
        self.overview_location_combo.addItem("Tüm Lokasyonlar", None)
        self._populate_locations(self.overview_location_combo)
        self.overview_location_combo.currentIndexChanged.connect(self._refresh_stock_overview)
        filter_layout.addWidget(loc_label)
        filter_layout.addWidget(self.overview_location_combo)

        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(Theme.get_button_style("secondary"))
        refresh_btn.clicked.connect(self._refresh_stock_overview)
        filter_layout.addWidget(refresh_btn)

        layout.addLayout(filter_layout)

        self.overview_table = QTableWidget()
        self.overview_table.setColumnCount(7)
        self.overview_table.setHorizontalHeaderLabels([
            "Ürün Adı", "SKU", "Barkod", "Lokasyon", "Miktar", "Toplam Stok", "Durum"
        ])
        header = self.overview_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 7):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.overview_table.setStyleSheet(self._table_style())
        self.overview_table.verticalHeader().setDefaultSectionSize(38)
        self.overview_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.overview_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.overview_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.overview_table.customContextMenuRequested.connect(self._show_overview_context_menu)
        layout.addWidget(self.overview_table)

        self._ov_page = 1
        self._ov_page_size = 100
        self._ov_filtered_data = []
        layout.addWidget(self._build_pagination_footer("ov"))

        self._overview_data = []
        self._refresh_stock_overview()
        return widget

    def _refresh_stock_overview(self):
        import json
        all_variants = self.stock_controller.variant_repo.get_all()
        selected_location = self.overview_location_combo.currentData()

        rows = []
        for v in all_variants:
            product = self.product_controller.product_repo.get_by_id(v["product_ID"])
            product_name = product["name"] if product else "—"
            quantities = json.loads(v.get("location_quantities", "{}"))
            total = sum(quantities.values())

            if not quantities:
                rows.append({
                    "variant_id": v["ID"],
                    "product_name": product_name,
                    "sku": v["sku"],
                    "barcode": v["barcode"],
                    "location_name": "—",
                    "quantity": 0,
                    "total": total
                })
                continue

            for loc_id, qty in quantities.items():
                if selected_location and int(loc_id) != selected_location:
                    continue
                location = self.location_controller.location_repo.get_by_id(int(loc_id))
                loc_name = location["name"] if location else f"ID: {loc_id}"
                rows.append({
                    "variant_id": v["ID"],
                    "product_name": product_name,
                    "sku": v["sku"],
                    "barcode": v["barcode"],
                    "location_name": loc_name,
                    "quantity": qty,
                    "total": total
                })

        self._overview_data = rows
        self._filter_stock_overview()

    def _filter_stock_overview(self):
        keyword = self.overview_search.text().strip().lower()
        data = self._overview_data

        if keyword:
            data = [r for r in data if
                    keyword in r["product_name"].lower() or
                    keyword in r["sku"].lower() or
                    keyword in r["barcode"].lower()]

        self._ov_filtered_data = data
        self._ov_page = 1
        self._render_overview_page()

    def _render_overview_page(self):
        data = self._ov_filtered_data
        total = len(data)
        total_pages = max(1, math.ceil(total / self._ov_page_size))
        if self._ov_page > total_pages:
            self._ov_page = total_pages

        start = (self._ov_page - 1) * self._ov_page_size
        end = start + self._ov_page_size
        page_data = data[start:end]

        self.overview_table.setRowCount(0)
        for r in page_data:
            row = self.overview_table.rowCount()
            self.overview_table.insertRow(row)
            name_item = QTableWidgetItem(r["product_name"])
            name_item.setData(Qt.UserRole, r["variant_id"])
            self.overview_table.setItem(row, 0, name_item)
            self.overview_table.setItem(row, 1, QTableWidgetItem(r["sku"]))
            self.overview_table.setItem(row, 2, QTableWidgetItem(r["barcode"]))
            self.overview_table.setItem(row, 3, QTableWidgetItem(r["location_name"]))

            qty_item = QTableWidgetItem(str(r["quantity"]))
            qty_item.setTextAlignment(Qt.AlignCenter)
            self.overview_table.setItem(row, 4, qty_item)

            total_item = QTableWidgetItem(str(r["total"]))
            total_item.setTextAlignment(Qt.AlignCenter)
            self.overview_table.setItem(row, 5, total_item)

            if r["total"] == 0:
                status = "Stok Yok"
                status_color = Theme.ERROR
            elif r["total"] <= 10:
                status = "Düşük"
                status_color = Theme.WARNING
            else:
                status = "Yeterli"
                status_color = Theme.SUCCESS

            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(self._qcolor(status_color))
            self.overview_table.setItem(row, 6, status_item)

        self._update_pagination_footer("ov", total, total_pages)


    def _build_stock_in_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        info = QLabel("Bir varyantı seçip belirlenen lokasyona stok girişi yapın.")
        info.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(12)

        self.in_barcode_input = QLineEdit()
        self.in_barcode_input.setPlaceholderText("Barkod okutun veya SKU yazın → Enter")
        self.in_barcode_input.setStyleSheet(self._input_style())
        self.in_barcode_input.returnPressed.connect(lambda: self._scan_barcode(self.in_barcode_input, self.in_variant_combo))
        form.addRow("🔍 Barkod/SKU:", self.in_barcode_input)

        self.in_variant_combo = QComboBox()
        self.in_variant_combo.setStyleSheet(self._combo_style())
        self._make_searchable(self.in_variant_combo)
        self._populate_variants(self.in_variant_combo)
        form.addRow("Varyant (SKU) *:", self.in_variant_combo)

        self.in_location_combo = QComboBox()
        self.in_location_combo.setStyleSheet(self._combo_style())
        self._populate_locations(self.in_location_combo)
        form.addRow("Lokasyon *:", self.in_location_combo)

        self.in_quantity = QSpinBox()
        self.in_quantity.setRange(1, 999999)
        self.in_quantity.setValue(1)
        self.in_quantity.setStyleSheet(self._input_style())
        form.addRow("Miktar *:", self.in_quantity)

        self.in_reason = QLineEdit()
        self.in_reason.setPlaceholderText("Tedarikçiden mal alımı, üretim vs.")
        self.in_reason.setStyleSheet(self._input_style())
        form.addRow("Açıklama:", self.in_reason)

        layout.addLayout(form)

        btn = QPushButton("➕ Stok Girişi Yap")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(42)
        btn.setStyleSheet(Theme.get_button_style("success"))
        btn.clicked.connect(self._on_stock_in)
        layout.addWidget(btn)

        layout.addStretch()
        return widget

    def _on_stock_in(self):
        variant_id = self.in_variant_combo.currentData()
        location_id = self.in_location_combo.currentData()
        quantity = self.in_quantity.value()
        reason = self.in_reason.text().strip()

        if not variant_id:
            QMessageBox.warning(self, "Hata", "Lütfen bir varyant seçiniz.")
            return
        if not location_id:
            QMessageBox.warning(self, "Hata", "Lütfen bir lokasyon seçiniz.")
            return

        result = self.stock_controller.stock_in(variant_id, location_id, quantity, reason)
        if result["success"]:
            QMessageBox.information(self, "Başarılı", result["message"])
            self.in_quantity.setValue(1)
            self.in_reason.clear()
            self._refresh_all()
        else:
            QMessageBox.warning(self, "Hata", result["message"])


    def _build_stock_out_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        info = QLabel("Bir varyantı seçip belirlenen lokasyondan stok çıkışı yapın.")
        info.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(12)

        self.out_barcode_input = QLineEdit()
        self.out_barcode_input.setPlaceholderText("Barkod okutun veya SKU yazın → Enter")
        self.out_barcode_input.setStyleSheet(self._input_style())
        self.out_barcode_input.returnPressed.connect(lambda: self._scan_barcode(self.out_barcode_input, self.out_variant_combo))
        form.addRow("🔍 Barkod/SKU:", self.out_barcode_input)

        self.out_variant_combo = QComboBox()
        self.out_variant_combo.setStyleSheet(self._combo_style())
        self._make_searchable(self.out_variant_combo)
        self._populate_variants(self.out_variant_combo)
        self.out_variant_combo.currentIndexChanged.connect(self._on_out_variant_changed)
        form.addRow("Varyant (SKU) *:", self.out_variant_combo)

        self.out_location_combo = QComboBox()
        self.out_location_combo.setStyleSheet(self._combo_style())
        form.addRow("Lokasyon *:", self.out_location_combo)

        self.out_current_stock_label = QLabel("Mevcut: —")
        self.out_current_stock_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-weight: bold;")
        form.addRow("", self.out_current_stock_label)

        self.out_quantity = QSpinBox()
        self.out_quantity.setRange(1, 999999)
        self.out_quantity.setValue(1)
        self.out_quantity.setStyleSheet(self._input_style())
        form.addRow("Miktar *:", self.out_quantity)

        self.out_reason = QLineEdit()
        self.out_reason.setPlaceholderText("Satış, fire, iade vs.")
        self.out_reason.setStyleSheet(self._input_style())
        form.addRow("Açıklama:", self.out_reason)

        layout.addLayout(form)

        btn = QPushButton("➖ Stok Çıkışı Yap")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(42)
        btn.setStyleSheet(Theme.get_button_style("danger"))
        btn.clicked.connect(self._on_stock_out)
        layout.addWidget(btn)

        layout.addStretch()
        return widget

    def _on_out_variant_changed(self):
        self.out_location_combo.clear()
        variant_id = self.out_variant_combo.currentData()
        if not variant_id:
            self.out_current_stock_label.setText("Mevcut: —")
            return

        result = self.stock_controller.get_variant_stock(variant_id)
        if not result["success"] or not result["data"]["locations"]:
            self.out_location_combo.addItem("Stok yok", None)
            self.out_current_stock_label.setText("Mevcut: 0")
            return

        for loc in result["data"]["locations"]:
            self.out_location_combo.addItem(
                f"{loc['location_name']} ({loc['quantity']} adet)",
                loc["location_id"]
            )
        self.out_current_stock_label.setText(f"Mevcut toplam: {result['data']['total_quantity']}")

    def _on_stock_out(self):
        variant_id = self.out_variant_combo.currentData()
        location_id = self.out_location_combo.currentData()
        quantity = self.out_quantity.value()
        reason = self.out_reason.text().strip()

        if not variant_id:
            QMessageBox.warning(self, "Hata", "Lütfen bir varyant seçiniz.")
            return
        if not location_id:
            QMessageBox.warning(self, "Hata", "Seçili lokasyonda stok yok.")
            return

        result = self.stock_controller.stock_out(variant_id, location_id, quantity, reason)
        if result["success"]:
            QMessageBox.information(self, "Başarılı", result["message"])
            self.out_quantity.setValue(1)
            self.out_reason.clear()
            self._on_out_variant_changed()
            self._refresh_all()
        else:
            QMessageBox.warning(self, "Hata", result["message"])


    def _build_transfer_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        info = QLabel("Bir lokasyondaki stoku başka bir lokasyona transfer edin.")
        info.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(12)

        self.transfer_barcode_input = QLineEdit()
        self.transfer_barcode_input.setPlaceholderText("Barkod okutun veya SKU yazın → Enter")
        self.transfer_barcode_input.setStyleSheet(self._input_style())
        self.transfer_barcode_input.returnPressed.connect(lambda: self._scan_barcode(self.transfer_barcode_input, self.transfer_variant_combo))
        form.addRow("🔍 Barkod/SKU:", self.transfer_barcode_input)

        self.transfer_variant_combo = QComboBox()
        self.transfer_variant_combo.setStyleSheet(self._combo_style())
        self._make_searchable(self.transfer_variant_combo)
        self._populate_variants(self.transfer_variant_combo)
        self.transfer_variant_combo.currentIndexChanged.connect(self._on_transfer_variant_changed)
        form.addRow("Varyant (SKU) *:", self.transfer_variant_combo)

        self.transfer_source_combo = QComboBox()
        self.transfer_source_combo.setStyleSheet(self._combo_style())
        form.addRow("Kaynak Lokasyon *:", self.transfer_source_combo)

        self.transfer_dest_combo = QComboBox()
        self.transfer_dest_combo.setStyleSheet(self._combo_style())
        self._populate_locations(self.transfer_dest_combo)
        form.addRow("Hedef Lokasyon *:", self.transfer_dest_combo)

        self.transfer_quantity = QSpinBox()
        self.transfer_quantity.setRange(1, 999999)
        self.transfer_quantity.setValue(1)
        self.transfer_quantity.setStyleSheet(self._input_style())
        form.addRow("Miktar *:", self.transfer_quantity)

        self.transfer_reason = QLineEdit()
        self.transfer_reason.setPlaceholderText("Transfer nedeni...")
        self.transfer_reason.setStyleSheet(self._input_style())
        form.addRow("Açıklama:", self.transfer_reason)

        layout.addLayout(form)

        btn = QPushButton("🔄 Transfer Et")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(42)
        btn.setStyleSheet(Theme.get_button_style("primary"))
        btn.clicked.connect(self._on_transfer)
        layout.addWidget(btn)

        layout.addStretch()
        return widget

    def _on_transfer_variant_changed(self):
        self.transfer_source_combo.clear()
        variant_id = self.transfer_variant_combo.currentData()
        if not variant_id:
            return

        result = self.stock_controller.get_variant_stock(variant_id)
        if not result["success"] or not result["data"]["locations"]:
            self.transfer_source_combo.addItem("Stok yok", None)
            return

        for loc in result["data"]["locations"]:
            self.transfer_source_combo.addItem(
                f"{loc['location_name']} ({loc['quantity']} adet)",
                loc["location_id"]
            )

    def _on_transfer(self):
        variant_id = self.transfer_variant_combo.currentData()
        source_id = self.transfer_source_combo.currentData()
        dest_id = self.transfer_dest_combo.currentData()
        quantity = self.transfer_quantity.value()
        reason = self.transfer_reason.text().strip()

        if not variant_id:
            QMessageBox.warning(self, "Hata", "Lütfen bir varyant seçiniz.")
            return
        if not source_id:
            QMessageBox.warning(self, "Hata", "Kaynak lokasyonda stok yok.")
            return
        if not dest_id:
            QMessageBox.warning(self, "Hata", "Lütfen hedef lokasyon seçiniz.")
            return

        result = self.stock_controller.stock_transfer(variant_id, source_id, dest_id, quantity, reason)
        if result["success"]:
            QMessageBox.information(self, "Başarılı", result["message"])
            self.transfer_quantity.setValue(1)
            self.transfer_reason.clear()
            self._on_transfer_variant_changed()
            self._refresh_all()
        else:
            QMessageBox.warning(self, "Hata", result["message"])


    def _build_adjustment_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        info = QLabel("Fiziksel sayım sonrası stok miktarını düzeltin. Fark otomatik hesaplanır.")
        info.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(12)

        self.adj_variant_combo = QComboBox()
        self.adj_variant_combo.setStyleSheet(self._combo_style())
        self._make_searchable(self.adj_variant_combo)
        self._populate_variants(self.adj_variant_combo)
        self.adj_variant_combo.currentIndexChanged.connect(self._on_adj_variant_changed)
        form.addRow("Varyant (SKU) *:", self.adj_variant_combo)

        self.adj_location_combo = QComboBox()
        self.adj_location_combo.setStyleSheet(self._combo_style())
        self._populate_locations(self.adj_location_combo)
        self.adj_location_combo.currentIndexChanged.connect(self._on_adj_location_changed)
        form.addRow("Lokasyon *:", self.adj_location_combo)

        self.adj_current_label = QLabel("Mevcut stok: —")
        self.adj_current_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-weight: bold; font-size: 14px;")
        form.addRow("", self.adj_current_label)

        self.adj_new_quantity = QSpinBox()
        self.adj_new_quantity.setRange(0, 999999)
        self.adj_new_quantity.setValue(0)
        self.adj_new_quantity.setStyleSheet(self._input_style())
        self.adj_new_quantity.valueChanged.connect(self._on_adj_quantity_changed)
        form.addRow("Sayılan Miktar *:", self.adj_new_quantity)

        self.adj_diff_label = QLabel("Fark: —")
        self.adj_diff_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-weight: bold; font-size: 14px;")
        form.addRow("", self.adj_diff_label)

        self.adj_reason = QLineEdit("Sayım düzeltmesi")
        self.adj_reason.setStyleSheet(self._input_style())
        form.addRow("Açıklama:", self.adj_reason)

        layout.addLayout(form)

        btn = QPushButton("📋 Sayım Düzeltmesi Uygula")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(42)
        btn.setStyleSheet(Theme.get_button_style("primary"))
        btn.clicked.connect(self._on_adjustment)
        layout.addWidget(btn)

        layout.addStretch()
        return widget

    def _on_adj_variant_changed(self):
        self._update_adj_current()

    def _on_adj_location_changed(self):
        self._update_adj_current()

    def _update_adj_current(self):
        import json
        variant_id = self.adj_variant_combo.currentData()
        location_id = self.adj_location_combo.currentData()

        if not variant_id or not location_id:
            self.adj_current_label.setText("Mevcut stok: —")
            self.adj_diff_label.setText("Fark: —")
            return

        variant = self.stock_controller.variant_repo.get_by_id(variant_id)
        if not variant:
            self.adj_current_label.setText("Mevcut stok: 0")
            return

        quantities = json.loads(variant.get("location_quantities", "{}"))
        current = quantities.get(str(location_id), 0)
        self.adj_current_label.setText(f"Mevcut stok: {current}")
        self._adj_current_qty = current
        self._on_adj_quantity_changed()

    def _on_adj_quantity_changed(self):
        current = getattr(self, '_adj_current_qty', 0)
        new_val = self.adj_new_quantity.value()
        diff = new_val - current

        if diff > 0:
            self.adj_diff_label.setText(f"Fark: +{diff} (stok artacak)")
            self.adj_diff_label.setStyleSheet(f"color: {Theme.SUCCESS}; font-weight: bold; font-size: 14px;")
        elif diff < 0:
            self.adj_diff_label.setText(f"Fark: {diff} (stok azalacak)")
            self.adj_diff_label.setStyleSheet(f"color: {Theme.ERROR}; font-weight: bold; font-size: 14px;")
        else:
            self.adj_diff_label.setText("Fark: 0 (değişiklik yok)")
            self.adj_diff_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-weight: bold; font-size: 14px;")

    def _on_adjustment(self):
        variant_id = self.adj_variant_combo.currentData()
        location_id = self.adj_location_combo.currentData()
        new_quantity = self.adj_new_quantity.value()
        reason = self.adj_reason.text().strip()

        if not variant_id:
            QMessageBox.warning(self, "Hata", "Lütfen bir varyant seçiniz.")
            return
        if not location_id:
            QMessageBox.warning(self, "Hata", "Lütfen bir lokasyon seçiniz.")
            return

        result = self.stock_controller.stock_adjustment(variant_id, location_id, new_quantity, reason)
        if result["success"]:
            QMessageBox.information(self, "Başarılı", result["message"])
            self._update_adj_current()
            self._refresh_all()
        else:
            QMessageBox.warning(self, "Hata", result["message"])


    def _build_movements_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        filter_layout = QHBoxLayout()

        filter_label = QLabel("Filtre:")
        filter_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        self.movements_filter_combo = QComboBox()
        self.movements_filter_combo.setStyleSheet(self._combo_style())
        self.movements_filter_combo.addItem("Tüm Hareketler", None)
        self.movements_filter_combo.addItem("➕ Giriş (IN)", "IN")
        self.movements_filter_combo.addItem("➖ Çıkış (OUT)", "OUT")
        self.movements_filter_combo.addItem("🔄 Transfer", "TRANSFER")
        self.movements_filter_combo.addItem("📋 Sayım Artış", "ADJUSTMENT_IN")
        self.movements_filter_combo.addItem("📋 Sayım Azalış", "ADJUSTMENT_OUT")
        self.movements_filter_combo.currentIndexChanged.connect(self._refresh_movements)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.movements_filter_combo)

        filter_layout.addStretch()

        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(Theme.get_button_style("secondary"))
        refresh_btn.clicked.connect(self._refresh_movements)
        filter_layout.addWidget(refresh_btn)

        layout.addLayout(filter_layout)

        self.movements_table = QTableWidget()
        self.movements_table.setColumnCount(8)
        self.movements_table.setHorizontalHeaderLabels([
            "Tarih", "SKU", "Hareket Tipi", "Miktar",
            "Kaynak", "Hedef", "Açıklama", "ID"
        ])
        header = self.movements_table.horizontalHeader()
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        for i in [0, 1, 2, 3, 4, 5, 7]:
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.movements_table.setStyleSheet(self._table_style())
        self.movements_table.verticalHeader().setDefaultSectionSize(36)
        self.movements_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.movements_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.movements_table)

        self._mv_page = 1
        self._mv_page_size = 100
        self._mv_filtered_data = []
        layout.addWidget(self._build_pagination_footer("mv"))

        self._refresh_movements()
        return widget

    def _refresh_movements(self):
        filter_type = self.movements_filter_combo.currentData()

        all_movements = self.stock_controller.movement_repo.get_all()
        all_movements.sort(key=lambda m: m.get("created_at", ""), reverse=True)

        if filter_type:
            all_movements = [m for m in all_movements if m.get("movement_type") == filter_type]

        self._mv_enriched_data = []
        type_labels = {
            "IN": ("➕ Giriş", Theme.SUCCESS),
            "OUT": ("➖ Çıkış", Theme.ERROR),
            "TRANSFER": ("🔄 Transfer", Theme.INFO),
            "ADJUSTMENT_IN": ("📋 Sayım +", Theme.SUCCESS),
            "ADJUSTMENT_OUT": ("📋 Sayım −", Theme.WARNING),
        }

        for m in all_movements:
            variant = self.stock_controller.variant_repo.get_by_id(m.get("variant_ID"))
            sku = variant["sku"] if variant else "—"

            m_type = m.get("movement_type", "")
            label, color = type_labels.get(m_type, (m_type, Theme.TEXT_PRIMARY))

            source_id = m.get("source_location_ID")
            if source_id:
                source = self.location_controller.location_repo.get_by_id(source_id)
                source_name = source["name"] if source else "—"
            else:
                source_name = "—"

            dest_id = m.get("destination_location_ID")
            if dest_id:
                dest = self.location_controller.location_repo.get_by_id(dest_id)
                dest_name = dest["name"] if dest else "—"
            else:
                dest_name = "—"

            self._mv_enriched_data.append({
                "date": m.get("created_at", ""),
                "sku": sku,
                "type_label": label,
                "type_color": color,
                "quantity": m.get("quantity", 0),
                "source": source_name,
                "dest": dest_name,
                "reason": m.get("reason", ""),
                "id": m.get("ID", ""),
            })

        self._mv_filtered_data = self._mv_enriched_data
        self._mv_page = 1
        self._render_movements_page()

    def _render_movements_page(self):
        data = self._mv_filtered_data
        total = len(data)
        total_pages = max(1, math.ceil(total / self._mv_page_size))
        if self._mv_page > total_pages:
            self._mv_page = total_pages

        start = (self._mv_page - 1) * self._mv_page_size
        end = start + self._mv_page_size
        page_data = data[start:end]

        self.movements_table.setRowCount(0)

        for m in page_data:
            row = self.movements_table.rowCount()
            self.movements_table.insertRow(row)

            self.movements_table.setItem(row, 0, QTableWidgetItem(m["date"]))
            self.movements_table.setItem(row, 1, QTableWidgetItem(m["sku"]))

            type_item = QTableWidgetItem(m["type_label"])
            type_item.setForeground(self._qcolor(m["type_color"]))
            type_item.setTextAlignment(Qt.AlignCenter)
            self.movements_table.setItem(row, 2, type_item)

            qty_item = QTableWidgetItem(str(m["quantity"]))
            qty_item.setTextAlignment(Qt.AlignCenter)
            self.movements_table.setItem(row, 3, qty_item)

            self.movements_table.setItem(row, 4, QTableWidgetItem(m["source"]))
            self.movements_table.setItem(row, 5, QTableWidgetItem(m["dest"]))
            self.movements_table.setItem(row, 6, QTableWidgetItem(m["reason"]))

            id_item = QTableWidgetItem(str(m["id"]))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.movements_table.setItem(row, 7, id_item)

        self._update_pagination_footer("mv", total, total_pages)


    def _show_overview_context_menu(self, pos):
        row = self.overview_table.rowAt(pos.y())
        if row < 0:
            return

        item = self.overview_table.item(row, 0)
        if not item:
            return
        variant_id = item.data(Qt.UserRole)
        sku = self.overview_table.item(row, 1).text() if self.overview_table.item(row, 1) else ""
        product_name = item.text()

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

        header_action = menu.addAction(f"📦 {product_name} ({sku})")
        header_action.setEnabled(False)
        menu.addSeparator()

        stock_in_action = menu.addAction("➕ Stok Giriş")
        stock_out_action = menu.addAction("➖ Stok Çıkış")
        transfer_action = menu.addAction("🔄 Transfer")
        adjustment_action = menu.addAction("📋 Sayım")

        action = menu.exec_(self.overview_table.viewport().mapToGlobal(pos))

        if action == stock_in_action:
            self._navigate_to_tab_with_variant(1, variant_id)
        elif action == stock_out_action:
            self._navigate_to_tab_with_variant(2, variant_id)
        elif action == transfer_action:
            self._navigate_to_tab_with_variant(3, variant_id)
        elif action == adjustment_action:
            self._navigate_to_tab_with_variant(4, variant_id)

    def _navigate_to_tab_with_variant(self, tab_index: int, variant_id: int):
        self.tabs.setCurrentIndex(tab_index)

        combo_map = {
            1: self.in_variant_combo,
            2: self.out_variant_combo,
            3: self.transfer_variant_combo,
            4: self.adj_variant_combo,
        }
        combo = combo_map.get(tab_index)
        if combo:
            for i in range(combo.count()):
                if combo.itemData(i) == variant_id:
                    combo.setCurrentIndex(i)
                    break


    def _build_pagination_footer(self, prefix: str) -> QFrame:
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

        total_label = QLabel("Toplam: 0 kayıt")
        total_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        layout.addWidget(total_label)
        setattr(self, f"_{prefix}_total_label", total_label)

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

        btn_first = QPushButton("«")
        btn_first.setToolTip("İlk Sayfa")
        btn_first.setCursor(Qt.PointingHandCursor)
        btn_first.setStyleSheet(pagination_style)
        btn_first.clicked.connect(lambda: self._pg_go(prefix, 1))
        layout.addWidget(btn_first)
        setattr(self, f"_{prefix}_btn_first", btn_first)

        btn_prev = QPushButton("‹ Önceki")
        btn_prev.setCursor(Qt.PointingHandCursor)
        btn_prev.setStyleSheet(pagination_style)
        btn_prev.clicked.connect(lambda: self._pg_go(prefix, getattr(self, f"_{prefix}_page") - 1))
        layout.addWidget(btn_prev)
        setattr(self, f"_{prefix}_btn_prev", btn_prev)

        page_spin = QSpinBox()
        page_spin.setRange(1, 1)
        page_spin.setValue(1)
        page_spin.setFixedWidth(60)
        page_spin.setAlignment(Qt.AlignCenter)
        page_spin.setStyleSheet(f"""
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
        page_spin.valueChanged.connect(lambda v: self._pg_go(prefix, v))
        layout.addWidget(page_spin)
        setattr(self, f"_{prefix}_page_spin", page_spin)

        page_info = QLabel("/ 1")
        page_info.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        layout.addWidget(page_info)
        setattr(self, f"_{prefix}_page_info", page_info)

        btn_next = QPushButton("Sonraki ›")
        btn_next.setCursor(Qt.PointingHandCursor)
        btn_next.setStyleSheet(pagination_style)
        btn_next.clicked.connect(lambda: self._pg_go(prefix, getattr(self, f"_{prefix}_page") + 1))
        layout.addWidget(btn_next)
        setattr(self, f"_{prefix}_btn_next", btn_next)

        btn_last = QPushButton("»")
        btn_last.setToolTip("Son Sayfa")
        btn_last.setCursor(Qt.PointingHandCursor)
        btn_last.setStyleSheet(pagination_style)
        layout.addWidget(btn_last)
        setattr(self, f"_{prefix}_btn_last", btn_last)

        sep = QLabel("|")
        sep.setStyleSheet(f"color: {Theme.BORDER}; background: transparent;")
        layout.addWidget(sep)

        size_label = QLabel("Sayfa:")
        size_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        layout.addWidget(size_label)

        size_combo = QComboBox()
        size_combo.addItems(["50", "100", "200", "500"])
        size_combo.setCurrentText(str(getattr(self, f"_{prefix}_page_size")))
        size_combo.setFixedWidth(70)
        size_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Theme.BG_SIDEBAR};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                selection-background-color: {Theme.BG_HOVER};
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox::down-arrow {{ image: none; }}
        """)
        size_combo.currentTextChanged.connect(lambda t: self._pg_size_changed(prefix, t))
        layout.addWidget(size_combo)

        btn_last.clicked.connect(lambda: self._pg_go(prefix, getattr(self, f"_{prefix}_page_spin").maximum()))

        return footer

    def _update_pagination_footer(self, prefix: str, total: int, total_pages: int):
        page = getattr(self, f"_{prefix}_page")
        page_size = getattr(self, f"_{prefix}_page_size")

        spin = getattr(self, f"_{prefix}_page_spin")
        spin.blockSignals(True)
        spin.setRange(1, total_pages)
        spin.setValue(page)
        spin.blockSignals(False)

        getattr(self, f"_{prefix}_page_info").setText(f"/ {total_pages}")
        getattr(self, f"_{prefix}_btn_first").setEnabled(page > 1)
        getattr(self, f"_{prefix}_btn_prev").setEnabled(page > 1)
        getattr(self, f"_{prefix}_btn_next").setEnabled(page < total_pages)
        getattr(self, f"_{prefix}_btn_last").setEnabled(page < total_pages)

        start = (page - 1) * page_size + 1
        end = min(page * page_size, total)
        if total == 0:
            getattr(self, f"_{prefix}_total_label").setText("Kayıt bulunamadı")
        else:
            getattr(self, f"_{prefix}_total_label").setText(
                f"Toplam {total} kayıttan {start}-{end} arası gösteriliyor")

    def _pg_go(self, prefix: str, page: int):
        total_pages = getattr(self, f"_{prefix}_page_spin").maximum()
        page = max(1, min(page, total_pages))
        current = getattr(self, f"_{prefix}_page")
        if page != current:
            setattr(self, f"_{prefix}_page", page)
            if prefix == "ov":
                self._render_overview_page()
            elif prefix == "mv":
                self._render_movements_page()

    def _pg_size_changed(self, prefix: str, text: str):
        try:
            new_size = int(text)
        except ValueError:
            return
        setattr(self, f"_{prefix}_page_size", new_size)
        setattr(self, f"_{prefix}_page", 1)
        if prefix == "ov":
            self._render_overview_page()
        elif prefix == "mv":
            self._render_movements_page()

    def _scan_barcode(self, input_field: QLineEdit, combo: QComboBox):
        text = input_field.text().strip()
        if not text:
            return

        all_variants = self.stock_controller.variant_repo.get_all()
        found_variant_id = None
        for v in all_variants:
            if (v.get("barcode", "") or "").strip() == text or (v.get("sku", "") or "").strip() == text:
                found_variant_id = v["ID"]
                break

        if found_variant_id:
            for i in range(combo.count()):
                if combo.itemData(i) == found_variant_id:
                    combo.setCurrentIndex(i)
                    input_field.setStyleSheet(self._input_style() + f"QLineEdit {{ border: 2px solid {Theme.SUCCESS}; }}")
                    input_field.clear()
                    return

        input_field.setStyleSheet(self._input_style() + f"QLineEdit {{ border: 2px solid {Theme.ERROR}; }}")
        QMessageBox.warning(self, "Bulunamadı", f"'{text}' barkod veya SKU ile eşleşen varyant bulunamadı.")

    def _make_searchable(self, combo: QComboBox):
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.NoInsert)
        combo.completer().setCompletionMode(QCompleter.PopupCompletion)
        combo.completer().setFilterMode(Qt.MatchContains)
        combo.lineEdit().setPlaceholderText("Yazarak arayın...")

    def _populate_variants(self, combo: QComboBox):
        combo.clear()
        combo.addItem("-- Varyant Seçiniz --", None)
        all_variants = self.stock_controller.variant_repo.get_all()
        for v in all_variants:
            product = self.product_controller.product_repo.get_by_id(v["product_ID"])
            product_name = product["name"] if product else "?"
            label = f"{product_name} — {v['sku']} ({v['barcode']})"
            combo.addItem(label, v["ID"])

    def _populate_locations(self, combo: QComboBox):
        result = self.location_controller.get_all_locations()
        if result["success"]:
            for loc in result["data"]:
                combo.addItem(loc["name"], loc["ID"])

    def _refresh_all(self):
        self._build_summary_cards()
        self._refresh_stock_overview()

    def _qcolor(self, hex_color: str):
        from PyQt5.QtGui import QColor
        return QColor(hex_color)

    def _input_style(self) -> str:
        return f"""
            QLineEdit, QSpinBox, QDoubleSpinBox {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.BORDER_RADIUS_SMALL}px;
                padding: 6px 10px;
                font-size: {Theme.FONT_SIZE_NORMAL}px;
            }}
        """

    def _combo_style(self) -> str:
        return f"""
            QComboBox {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.BORDER_RADIUS_SMALL}px;
                padding: 6px 10px;
                font-size: {Theme.FONT_SIZE_NORMAL}px;
                min-width: 200px;
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

    def _table_style(self) -> str:
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
                padding: 4px;
            }}
            QHeaderView::section {{
                background-color: {Theme.BG_SIDEBAR};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                padding: 6px;
                font-weight: bold;
            }}
        """
