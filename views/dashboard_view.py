from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QScrollArea, QFrame, QSizePolicy, QGridLayout)
from PyQt5.QtCore import Qt, QTimer, QRectF, QRect, QPointF
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QBrush, QPainterPath, QLinearGradient
from utils.theme import Theme
from datetime import datetime, timedelta
import json
import math


class BarChartWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self.data = []
        self.max_value = 0

    def set_data(self, data: list):
        self.data = data
        self.max_value = max((v for _, v in data), default=1)
        if self.max_value == 0:
            self.max_value = 1
        self.update()

    def paintEvent(self, event):
        if not self.data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        margin_left = 60
        margin_right = 15
        margin_top = 15
        margin_bottom = 40

        chart_w = w - margin_left - margin_right
        chart_h = h - margin_top - margin_bottom

        n = len(self.data)
        if n == 0:
            painter.end()
            return

        bar_width = max(20, min(50, chart_w // n - 12))
        spacing = (chart_w - n * bar_width) / (n + 1)

        num_lines = 4
        for i in range(num_lines + 1):
            y = margin_top + chart_h - (i * chart_h / num_lines)
            painter.setPen(QPen(QColor(Theme.BORDER), 1, Qt.DotLine))
            painter.drawLine(int(margin_left), int(y), int(w - margin_right), int(y))

            val = self.max_value * i / num_lines
            painter.setPen(QPen(QColor(Theme.TEXT_MUTED), 1))
            painter.setFont(QFont("Segoe UI", 9))
            if val >= 1000:
                label = f"{val / 1000:.1f}K"
            else:
                label = f"{val:.0f}"
            painter.drawText(QRect(0, int(y) - 10, margin_left - 8, 20),
                             Qt.AlignRight | Qt.AlignVCenter, label)

        for i, (label, value) in enumerate(self.data):
            x = margin_left + spacing + i * (bar_width + spacing)
            bar_h = (value / self.max_value) * chart_h if self.max_value > 0 else 0
            y = margin_top + chart_h - bar_h

            gradient = QLinearGradient(x, y, x, margin_top + chart_h)
            gradient.setColorAt(0, QColor(Theme.SUCCESS))
            gradient.setColorAt(1, QColor(78, 204, 163, 100))

            path = QPainterPath()
            radius = min(4, bar_width / 4)
            rect = QRectF(x, y, bar_width, bar_h)
            path.addRoundedRect(rect, radius, radius)
            painter.fillPath(path, QBrush(gradient))

            if value > 0:
                painter.setPen(QPen(QColor(Theme.TEXT_PRIMARY), 1))
                painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
                if value >= 1000:
                    val_text = f"{value / 1000:.1f}K"
                else:
                    val_text = f"{value:.0f}"
                painter.drawText(QRectF(x - 5, y - 18, bar_width + 10, 16),
                                 Qt.AlignCenter, val_text)

            painter.setPen(QPen(QColor(Theme.TEXT_SECONDARY), 1))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(QRectF(x - 10, margin_top + chart_h + 5, bar_width + 20, 30),
                             Qt.AlignCenter, label)

        painter.end()


class DonutChartWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self.setMinimumWidth(200)
        self.data = []
        self.total = 0
        self.center_text = "0"
        self.center_subtitle = "Toplam"

    def set_data(self, data: list, center_text: str = "", center_subtitle: str = "Toplam"):
        self.data = [(l, v, c) for l, v, c in data if v > 0]
        self.total = sum(v for _, v, _ in self.data)
        self.center_text = center_text or str(self.total)
        self.center_subtitle = center_subtitle
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        size = min(w, h) - 20
        outer_r = size / 2
        inner_r = outer_r * 0.62

        cx = w / 2
        cy = h / 2
        rect = QRectF(cx - outer_r, cy - outer_r, outer_r * 2, outer_r * 2)

        if not self.data or self.total == 0:
            painter.setPen(QPen(QColor(Theme.BORDER), 2))
            painter.setBrush(QBrush(QColor(Theme.BG_DARK)))
            painter.drawEllipse(rect)

            inner_rect = QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2)
            painter.setBrush(QBrush(QColor(Theme.BG_CARD)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(inner_rect)

            painter.setPen(QPen(QColor(Theme.TEXT_MUTED), 1))
            painter.setFont(QFont("Segoe UI", 12))
            painter.drawText(rect, Qt.AlignCenter, "Veri yok")
            painter.end()
            return

        gap_angle = 2 * 16

        start_angle = 90 * 16
        for label, value, color in self.data:
            span = int((value / self.total) * 360 * 16)
            if span <= gap_angle:
                start_angle -= span
                continue

            actual_span = span - gap_angle

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(color)))
            painter.drawPie(rect, start_angle, -actual_span)
            start_angle -= span

        inner_rect = QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2)
        painter.setBrush(QBrush(QColor(Theme.BG_CARD)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(inner_rect)

        painter.setPen(QPen(QColor(Theme.TEXT_PRIMARY), 1))
        painter.setFont(QFont("Segoe UI", 22, QFont.Bold))
        text_rect = QRectF(cx - inner_r, cy - 18, inner_r * 2, 30)
        painter.drawText(text_rect, Qt.AlignCenter, self.center_text)

        painter.setPen(QPen(QColor(Theme.TEXT_MUTED), 1))
        painter.setFont(QFont("Segoe UI", 10))
        sub_rect = QRectF(cx - inner_r, cy + 12, inner_r * 2, 20)
        painter.drawText(sub_rect, Qt.AlignCenter, self.center_subtitle)

        painter.end()


class HorizontalBarWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = []
        self.max_value = 0

    def set_data(self, data: list):
        self.data = data[:8]
        self.max_value = max((v for _, v, _ in self.data), default=1)
        if self.max_value == 0:
            self.max_value = 1
        row_h = 34
        self.setFixedHeight(max(100, len(self.data) * row_h + 10))
        self.update()

    def paintEvent(self, event):
        if not self.data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        label_width = 120
        value_width = 45
        bar_area = w - label_width - value_width - 20
        row_h = 32
        bar_h = 18

        for i, (label, value, color) in enumerate(self.data):
            y = i * row_h + 5

            painter.setPen(QPen(QColor(Theme.TEXT_SECONDARY), 1))
            painter.setFont(QFont("Segoe UI", 10))
            display_label = label if len(label) <= 14 else label[:12] + ".."
            painter.drawText(QRect(4, y, label_width - 8, row_h),
                             Qt.AlignVCenter | Qt.AlignLeft, display_label)

            bar_x = label_width
            bar_y = y + (row_h - bar_h) // 2
            bg_rect = QRectF(bar_x, bar_y, bar_area, bar_h)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(Theme.BG_DARK)))
            path_bg = QPainterPath()
            path_bg.addRoundedRect(bg_rect, 4, 4)
            painter.drawPath(path_bg)

            bar_w = (value / self.max_value) * bar_area
            if bar_w > 0:
                gradient = QLinearGradient(bar_x, bar_y, bar_x + bar_w, bar_y)
                gradient.setColorAt(0, QColor(color))
                c2 = QColor(color)
                c2.setAlpha(160)
                gradient.setColorAt(1, c2)

                bar_rect = QRectF(bar_x, bar_y, max(bar_w, 6), bar_h)
                path_bar = QPainterPath()
                path_bar.addRoundedRect(bar_rect, 4, 4)
                painter.fillPath(path_bar, QBrush(gradient))

            painter.setPen(QPen(QColor(Theme.TEXT_PRIMARY), 1))
            painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
            painter.drawText(QRect(int(label_width + bar_area + 6), y, value_width, row_h),
                             Qt.AlignVCenter | Qt.AlignLeft, str(int(value)))

        painter.end()


class MiniSparkline(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(35)
        self.data = []
        self.color = QColor(Theme.SUCCESS)

    def set_data(self, data: list, color: str = None):
        self.data = data
        if color:
            self.color = QColor(color)
        self.update()

    def paintEvent(self, event):
        if len(self.data) < 2:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        margin = 4

        max_val = max(self.data) if self.data else 1
        min_val = min(self.data) if self.data else 0
        if max_val == 0 and min_val == 0:
            max_val = 1
        val_range = max_val - min_val
        if val_range == 0:
            val_range = max_val or 1

        n = len(self.data)
        step_x = (w - 2 * margin) / max(n - 1, 1)

        points = []
        for i, val in enumerate(self.data):
            x = margin + i * step_x
            y = margin + (1 - (val - min_val) / val_range) * (h - 2 * margin)
            points.append(QPointF(x, y))

        fill_path = QPainterPath()
        fill_path.moveTo(points[0])
        for p in points[1:]:
            fill_path.lineTo(p)
        fill_path.lineTo(QPointF(points[-1].x(), h))
        fill_path.lineTo(QPointF(points[0].x(), h))
        fill_path.closeSubpath()

        fill_color = QColor(self.color)
        fill_color.setAlpha(40)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(fill_color))
        painter.drawPath(fill_path)

        line_path = QPainterPath()
        line_path.moveTo(points[0])
        for p in points[1:]:
            line_path.lineTo(p)

        pen = QPen(self.color, 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(line_path)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.color))
        painter.drawEllipse(points[-1], 3, 3)

        painter.end()


class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._load_data()

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._load_data)
        self.refresh_timer.start(60000)

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {Theme.BG_DARK};
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
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        content = QWidget()
        self.main_layout = QVBoxLayout(content)
        self.main_layout.setContentsMargins(25, 20, 25, 25)
        self.main_layout.setSpacing(18)

        self._create_stat_cards()

        self._create_charts_section()

        self._create_middle_section()

        self._create_bottom_section()

        self.main_layout.addStretch()

        scroll.setWidget(content)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)


    def _create_stat_cards(self):
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)

        self.card_total_products = self._create_single_stat_card(
            "📦", "Toplam Ürün", "0", "Aktif: 0", Theme.ACCENT
        )
        cards_layout.addWidget(self.card_total_products["widget"])

        self.card_today_orders = self._create_single_stat_card(
            "📋", "Bugünkü Siparişler", "0", "Bekleyen: 0", Theme.INFO
        )
        cards_layout.addWidget(self.card_today_orders["widget"])

        self.card_today_revenue = self._create_single_stat_card(
            "💰", "Bugünkü Ciro", "0,00 ₺", "Aylık: 0,00 ₺", Theme.SUCCESS
        )
        cards_layout.addWidget(self.card_today_revenue["widget"])

        self.card_low_stock = self._create_single_stat_card(
            "⚠️", "Düşük Stok", "0", "Kritik: 0", Theme.WARNING
        )
        cards_layout.addWidget(self.card_low_stock["widget"])

        self.main_layout.addLayout(cards_layout)

    def _create_single_stat_card(self, icon: str, title: str, value: str,
                                  subtitle: str, color: str) -> dict:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border-left: 4px solid {color};
                border-radius: {Theme.BORDER_RADIUS}px;
                padding: {Theme.CARD_PADDING}px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 12, 20, 10)
        layout.setSpacing(4)

        top_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 22px; background: transparent;")
        top_layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; background: transparent;")
        top_layout.addWidget(title_label)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        value_label = QLabel(value)
        value_label.setFont(QFont("Segoe UI", 26, QFont.Bold))
        value_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(value_label)

        sparkline = MiniSparkline()
        sparkline.set_data([0, 0], color)
        layout.addWidget(sparkline)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px; background: transparent;")
        layout.addWidget(subtitle_label)

        return {
            "widget": card,
            "value_label": value_label,
            "subtitle_label": subtitle_label,
            "sparkline": sparkline,
        }


    def _create_charts_section(self):
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(15)

        revenue_card = QFrame()
        revenue_card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border-radius: {Theme.BORDER_RADIUS}px;
            }}
        """)
        revenue_layout = QVBoxLayout(revenue_card)
        revenue_layout.setContentsMargins(20, 16, 20, 16)
        revenue_layout.setSpacing(8)

        rev_header = QHBoxLayout()
        rev_title = QLabel("📊  Haftalık Ciro")
        rev_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        rev_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; background: transparent;")
        rev_header.addWidget(rev_title)
        rev_header.addStretch()

        self.rev_total_label = QLabel("Toplam: 0,00 ₺")
        self.rev_total_label.setStyleSheet(f"color: {Theme.SUCCESS}; font-size: 12px; font-weight: bold; background: transparent;")
        rev_header.addWidget(self.rev_total_label)
        revenue_layout.addLayout(rev_header)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {Theme.BORDER};")
        revenue_layout.addWidget(sep)

        self.bar_chart = BarChartWidget()
        self.bar_chart.setMinimumHeight(230)
        revenue_layout.addWidget(self.bar_chart)

        charts_layout.addWidget(revenue_card, 3)

        status_card = QFrame()
        status_card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border-radius: {Theme.BORDER_RADIUS}px;
            }}
        """)
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(20, 16, 20, 16)
        status_layout.setSpacing(8)

        st_title = QLabel("🎯  Sipariş Durumları")
        st_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        st_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; background: transparent;")
        status_layout.addWidget(st_title)

        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background-color: {Theme.BORDER};")
        status_layout.addWidget(sep2)

        self.donut_chart = DonutChartWidget()
        self.donut_chart.setMinimumHeight(190)
        status_layout.addWidget(self.donut_chart)

        self.donut_legend_layout = QVBoxLayout()
        self.donut_legend_layout.setSpacing(4)
        status_layout.addLayout(self.donut_legend_layout)

        charts_layout.addWidget(status_card, 2)

        self.main_layout.addLayout(charts_layout)


    def _create_middle_section(self):
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(15)

        orders_card = self._create_table_card(
            "🕐  Son Siparişler",
            ["Sipariş No", "Müşteri", "Tutar", "Durum", "Tarih"]
        )
        self.orders_table = orders_card["table"]
        middle_layout.addWidget(orders_card["widget"])

        stock_card = self._create_table_card(
            "⚠️  Düşük Stok Uyarıları",
            ["Ürün", "SKU", "Mevcut", "Minimum", "Durum"]
        )
        self.low_stock_table = stock_card["table"]
        middle_layout.addWidget(stock_card["widget"])

        self.main_layout.addLayout(middle_layout)


    def _create_bottom_section(self):
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(15)

        cat_card = QFrame()
        cat_card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border-radius: {Theme.BORDER_RADIUS}px;
            }}
        """)
        cat_layout = QVBoxLayout(cat_card)
        cat_layout.setContentsMargins(20, 16, 20, 16)
        cat_layout.setSpacing(8)

        cat_title = QLabel("📂  Kategoriye Göre Ürünler")
        cat_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        cat_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; background: transparent;")
        cat_layout.addWidget(cat_title)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {Theme.BORDER};")
        cat_layout.addWidget(sep)

        self.h_bar_chart = HorizontalBarWidget()
        cat_layout.addWidget(self.h_bar_chart)
        cat_layout.addStretch()

        bottom_layout.addWidget(cat_card)

        summary_card = self._create_summary_card()
        self.summary_widget = summary_card
        bottom_layout.addWidget(summary_card["widget"])

        activity_card = self._create_table_card(
            "🕐  Son Aktiviteler",
            ["Zaman", "Kullanıcı", "İşlem", "Detay"]
        )
        self.activity_table = activity_card["table"]
        bottom_layout.addWidget(activity_card["widget"])

        self.main_layout.addLayout(bottom_layout)

    def _create_summary_card(self) -> dict:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border-radius: {Theme.BORDER_RADIUS}px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(5)

        title = QLabel("📊  Hızlı Özet")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {Theme.BORDER};")
        layout.addWidget(sep)
        layout.addSpacing(8)

        summary_items = [
            ("👥", "Toplam Müşteri", "0"),
            ("🚚", "Toplam Tedarikçi", "0"),
            ("📂", "Toplam Kategori", "0"),
            ("🏷️", "Toplam Marka", "0"),
            ("👔", "Toplam Çalışan", "0"),
            ("📍", "Toplam Lokasyon", "0"),
        ]

        self.summary_labels = {}
        for icon, label_text, default_value in summary_items:
            row = QHBoxLayout()
            row.setSpacing(10)

            icon_lbl = QLabel(icon)
            icon_lbl.setFixedWidth(25)
            icon_lbl.setStyleSheet("font-size: 16px; background: transparent;")
            row.addWidget(icon_lbl)

            text_lbl = QLabel(label_text)
            text_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 13px; background: transparent;")
            row.addWidget(text_lbl)

            row.addStretch()

            value_lbl = QLabel(default_value)
            value_lbl.setFont(QFont("Segoe UI", 14, QFont.Bold))
            value_lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; background: transparent;")
            row.addWidget(value_lbl)

            self.summary_labels[label_text] = value_lbl
            layout.addLayout(row)

            line = QFrame()
            line.setFixedHeight(1)
            line.setStyleSheet(f"background-color: {Theme.BORDER}; margin: 4px 0px;")
            layout.addWidget(line)

        layout.addStretch()

        return {"widget": card}


    def _create_table_card(self, title: str, columns: list[str]) -> dict:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border-radius: {Theme.BORDER_RADIUS}px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(title_label)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {Theme.BORDER};")
        layout.addWidget(sep)

        table = QTableWidget()
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.setRowCount(0)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setMinimumHeight(200)

        header = table.horizontalHeader()
        for i in range(len(columns)):
            header.setSectionResizeMode(i, QHeaderView.Stretch)

        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Theme.BG_CARD};
                color: {Theme.TEXT_PRIMARY};
                border: none;
                gridline-color: transparent;
                selection-background-color: {Theme.ACCENT_LIGHT};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {Theme.BORDER};
            }}
            QTableWidget::item:alternate {{
                background-color: {Theme.BG_DARK};
            }}
            QHeaderView::section {{
                background-color: {Theme.BG_CARD};
                color: {Theme.TEXT_SECONDARY};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {Theme.ACCENT};
                font-weight: bold;
                font-size: 12px;
            }}
        """)

        empty_label = QLabel("Henüz veri yok")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 13px; padding: 20px; background: transparent;")

        layout.addWidget(table)
        layout.addWidget(empty_label)

        return {
            "widget": card,
            "table": table,
            "empty_label": empty_label
        }


    def _load_data(self):
        try:
            self._load_stat_cards()
            self._load_weekly_revenue()
            self._load_order_status_chart()
            self._load_category_distribution()
            self._load_recent_orders()
            self._load_low_stock()
            self._load_summary()
            self._load_recent_activity()
        except Exception as e:
            print(f"[ERROR] Dashboard veri yükleme hatası: {e}")


    def _load_stat_cards(self):
        from database.product_repository import ProductRepository
        from database.order_repository import OrderRepository
        from database.order_item_repository import OrderItemRepository
        from database.payment_repository import PaymentRepository
        from database.variant_repository import VariantRepository

        product_repo = ProductRepository()
        order_repo = OrderRepository()
        order_item_repo = OrderItemRepository()
        payment_repo = PaymentRepository()
        variant_repo = VariantRepository()

        all_products = product_repo.get_all()
        active_products = [p for p in all_products if p.get("is_active", 1) == 1]
        self.card_total_products["value_label"].setText(str(len(all_products)))
        self.card_total_products["subtitle_label"].setText(f"Aktif: {len(active_products)}")

        prod_spark = []
        for i in range(6, -1, -1):
            d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            count = len([p for p in all_products if p.get("created_at", "").startswith(d)])
            prod_spark.append(count)
        self.card_total_products["sparkline"].set_data(prod_spark, Theme.ACCENT)

        today = datetime.now().strftime("%Y-%m-%d")
        all_orders = order_repo.get_all()
        today_orders = [o for o in all_orders if o.get("created_at", "").startswith(today)]
        pending_orders = [o for o in all_orders if o.get("status") == "pending"]
        self.card_today_orders["value_label"].setText(str(len(today_orders)))
        self.card_today_orders["subtitle_label"].setText(f"Bekleyen: {len(pending_orders)}")

        order_spark = []
        for i in range(6, -1, -1):
            d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            count = len([o for o in all_orders if o.get("created_at", "").startswith(d)])
            order_spark.append(count)
        self.card_today_orders["sparkline"].set_data(order_spark, Theme.INFO)

        all_payments = [p for p in payment_repo.get_all() if p.get("status") == "completed"]
        today_revenue = sum(float(p.get("amount", 0))
                           for p in all_payments if (p.get("payment_date") or "").startswith(today))
        month = datetime.now().strftime("%Y-%m")
        month_revenue = sum(float(p.get("amount", 0))
                           for p in all_payments if (p.get("payment_date") or "").startswith(month))
        self.card_today_revenue["value_label"].setText(f"{today_revenue:,.2f} ₺")
        self.card_today_revenue["subtitle_label"].setText(f"Aylık: {month_revenue:,.2f} ₺")

        rev_spark = []
        for i in range(6, -1, -1):
            d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_rev = sum(float(p.get("amount", 0))
                         for p in all_payments if (p.get("payment_date") or "").startswith(d))
            rev_spark.append(day_rev)
        self.card_today_revenue["sparkline"].set_data(rev_spark, Theme.SUCCESS)

        all_variants = variant_repo.get_all()
        low_stock_count = 0
        critical_count = 0
        for v in all_variants:
            quantities = json.loads(v.get("location_quantities", "{}"))
            total_qty = sum(int(q) for q in quantities.values()) if quantities else 0
            if total_qty == 0:
                critical_count += 1
                low_stock_count += 1
            elif total_qty <= 10:
                low_stock_count += 1

        self.card_low_stock["value_label"].setText(str(low_stock_count))
        self.card_low_stock["subtitle_label"].setText(f"Kritik: {critical_count}")
        self.card_low_stock["sparkline"].set_data([low_stock_count] * 7, Theme.WARNING)


    def _load_weekly_revenue(self):
        from database.payment_repository import PaymentRepository

        payment_repo = PaymentRepository()
        all_payments = [p for p in payment_repo.get_all() if p.get("status") == "completed"]

        data = []
        week_total = 0
        day_names_tr = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]

        for i in range(6, -1, -1):
            d = datetime.now() - timedelta(days=i)
            d_str = d.strftime("%Y-%m-%d")
            day_revenue = sum(float(p.get("amount", 0))
                              for p in all_payments if (p.get("payment_date") or "").startswith(d_str))
            week_total += day_revenue

            day_name = day_names_tr[d.weekday()]
            day_num = d.strftime("%d")
            label = f"{day_name}\n{day_num}"
            data.append((label, day_revenue))

        self.bar_chart.set_data(data)
        self.rev_total_label.setText(f"Toplam: {week_total:,.2f} ₺")


    def _load_order_status_chart(self):
        from database.order_repository import OrderRepository

        order_repo = OrderRepository()
        all_orders = order_repo.get_all()

        status_config = [
            ("pending", "Beklemede", Theme.WARNING),
            ("confirmed", "Onaylandı", "#5dade2"),
            ("preparing", "Hazırlanıyor", Theme.INFO),
            ("shipped", "Kargoda", "#a29bfe"),
            ("delivered", "Teslim Edildi", "#55efc4"),
            ("completed", "Tamamlandı", Theme.SUCCESS),
            ("cancelled", "İptal", Theme.ERROR),
            ("refunded", "İade", "#fd79a8"),
        ]

        chart_data = []
        for status_key, label, color in status_config:
            count = len([o for o in all_orders if o.get("status") == status_key])
            chart_data.append((label, count, color))

        total = len(all_orders)
        self.donut_chart.set_data(chart_data, str(total), "Sipariş")

        while self.donut_legend_layout.count():
            child = self.donut_legend_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for label, count, color in chart_data:
            if count == 0:
                continue
            row_w = QWidget()
            row_w.setStyleSheet("background: transparent;")
            row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(0, 2, 0, 2)
            row_l.setSpacing(8)

            dot = QLabel("●")
            dot.setFixedWidth(16)
            dot.setStyleSheet(f"color: {color}; font-size: 12px; background: transparent;")
            row_l.addWidget(dot)

            name = QLabel(label)
            name.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; background: transparent;")
            row_l.addWidget(name)

            row_l.addStretch()

            val = QLabel(str(count))
            val.setFont(QFont("Segoe UI", 11, QFont.Bold))
            val.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; background: transparent;")
            row_l.addWidget(val)

            pct = f"{count / total * 100:.0f}%" if total > 0 else "0%"
            pct_lbl = QLabel(pct)
            pct_lbl.setFixedWidth(35)
            pct_lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 10px; background: transparent;")
            row_l.addWidget(pct_lbl)

            self.donut_legend_layout.addWidget(row_w)


    def _load_category_distribution(self):
        from database.product_repository import ProductRepository
        from database.category_repository import CategoryRepository

        product_repo = ProductRepository()
        category_repo = CategoryRepository()

        all_products = product_repo.get_all()
        all_categories = category_repo.get_all()

        cat_map = {c["ID"]: c.get("name", "?") for c in all_categories}

        cat_counts = {}
        for p in all_products:
            cid = p.get("main_category_ID")
            cat_name = cat_map.get(cid, "Diğer")
            cat_counts[cat_name] = cat_counts.get(cat_name, 0) + 1

        sorted_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)

        colors = [Theme.ACCENT, Theme.INFO, Theme.SUCCESS, Theme.WARNING,
                  "#a29bfe", "#fd79a8", "#55efc4", "#e17055"]

        chart_data = []
        for i, (name, count) in enumerate(sorted_cats[:8]):
            color = colors[i % len(colors)]
            chart_data.append((name, count, color))

        self.h_bar_chart.set_data(chart_data)


    def _load_recent_orders(self):
        from database.order_repository import OrderRepository
        from database.order_item_repository import OrderItemRepository
        from database.customer_repository import CustomerRepository

        order_repo = OrderRepository()
        order_item_repo = OrderItemRepository()
        customer_repo = CustomerRepository()

        orders = order_repo.get_all()
        orders.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        recent = orders[:10]

        table = self.orders_table
        table.setRowCount(len(recent))

        status_map = {
            "pending": ("Beklemede", Theme.WARNING),
            "confirmed": ("Onaylandı", Theme.INFO),
            "preparing": ("Hazırlanıyor", Theme.INFO),
            "shipped": ("Kargoda", Theme.ACCENT),
            "delivered": ("Teslim Edildi", Theme.SUCCESS),
            "completed": ("Tamamlandı", Theme.SUCCESS),
            "cancelled": ("İptal", Theme.ERROR),
        }

        for row, order in enumerate(recent):
            order_no = QTableWidgetItem(f"#{order.get('ID', '')}")
            order_no.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 0, order_no)

            customer_id = order.get("customer_ID")
            customer_name = "-"
            if customer_id:
                customer = customer_repo.get_by_id(customer_id)
                if customer:
                    customer_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}"
            table.setItem(row, 1, QTableWidgetItem(customer_name))

            amount = order_item_repo.get_order_total(order.get("ID", 0))
            discount = float(order.get("discount_price", 0))
            net_amount = max(amount - discount, 0)
            amount_item = QTableWidgetItem(f"{net_amount:,.2f} ₺")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(row, 2, amount_item)

            status = order.get("status", "pending")
            status_text, status_color = status_map.get(status, ("Bilinmiyor", Theme.TEXT_MUTED))
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(self._color_from_hex(status_color))
            table.setItem(row, 3, status_item)

            date = order.get("created_at", "")[:16]
            table.setItem(row, 4, QTableWidgetItem(date))


    def _load_low_stock(self):
        from database.variant_repository import VariantRepository
        from database.product_repository import ProductRepository

        variant_repo = VariantRepository()
        product_repo = ProductRepository()

        all_variants = variant_repo.get_all()
        low_stock_items = []

        for v in all_variants:
            quantities = json.loads(v.get("location_quantities", "{}"))
            total_qty = sum(int(q) for q in quantities.values()) if quantities else 0
            if total_qty <= 10:
                product = product_repo.get_by_id(v.get("product_ID"))
                product_name = product.get("name", "?") if product else "?"
                low_stock_items.append({
                    "product_name": product_name,
                    "sku": v.get("sku", "-"),
                    "current": total_qty,
                    "minimum": 10,
                    "critical": total_qty == 0
                })

        low_stock_items.sort(key=lambda x: x["current"])

        table = self.low_stock_table
        table.setRowCount(len(low_stock_items[:10]))

        for row, item in enumerate(low_stock_items[:10]):
            table.setItem(row, 0, QTableWidgetItem(item["product_name"]))
            table.setItem(row, 1, QTableWidgetItem(item["sku"]))

            current_item = QTableWidgetItem(str(item["current"]))
            current_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 2, current_item)

            min_item = QTableWidgetItem(str(item["minimum"]))
            min_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 3, min_item)

            if item["critical"]:
                status_item = QTableWidgetItem("🔴 Kritik")
                status_item.setForeground(self._color_from_hex(Theme.ERROR))
            else:
                status_item = QTableWidgetItem("🟡 Düşük")
                status_item.setForeground(self._color_from_hex(Theme.WARNING))
            status_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 4, status_item)


    def _load_summary(self):
        from database.customer_repository import CustomerRepository
        from database.supplier_repository import SupplierRepository
        from database.category_repository import CategoryRepository
        from database.brand_repository import BrandRepository
        from database.employee_repository import EmployeeRepository
        from database.location_repository import LocationRepository

        counts = {
            "Toplam Müşteri": len(CustomerRepository().get_all()),
            "Toplam Tedarikçi": len(SupplierRepository().get_all()),
            "Toplam Kategori": len(CategoryRepository().get_all()),
            "Toplam Marka": len(BrandRepository().get_all()),
            "Toplam Çalışan": len(EmployeeRepository().get_all()),
            "Toplam Lokasyon": len(LocationRepository().get_all()),
        }

        for label_text, count in counts.items():
            if label_text in self.summary_labels:
                self.summary_labels[label_text].setText(str(count))


    def _load_recent_activity(self):
        from utils.logger import Logger

        logger = Logger()
        table = self.activity_table

        try:
            lines = logger.get_logs()

            recent_lines = [l.strip() for l in lines if l.strip()]
            recent_lines = recent_lines[-10:]
            recent_lines.reverse()

            table.setRowCount(len(recent_lines))

            for row, line in enumerate(recent_lines):
                parts = line.split("] ")
                if len(parts) >= 4:
                    time_str = parts[0].replace("[", "")
                    user = parts[2].replace("[", "")
                    rest = "] ".join(parts[3:])
                    detail = rest.replace("[", "").replace("]", "").strip()

                    time_item = QTableWidgetItem(time_str[-8:])
                    time_item.setTextAlignment(Qt.AlignCenter)
                    table.setItem(row, 0, time_item)

                    table.setItem(row, 1, QTableWidgetItem(user))

                    action = detail[:40] + "..." if len(detail) > 40 else detail
                    table.setItem(row, 2, QTableWidgetItem(action))

                    detail_text = detail.split(" - ", 1)[1][:30] if " - " in detail else ""
                    table.setItem(row, 3, QTableWidgetItem(detail_text))
                else:
                    table.setItem(row, 0, QTableWidgetItem(""))
                    table.setItem(row, 1, QTableWidgetItem(""))
                    table.setItem(row, 2, QTableWidgetItem(line[:50]))
                    table.setItem(row, 3, QTableWidgetItem(""))

        except Exception as e:
            print(f"[ERROR] Aktivite yükleme hatası: {e}")
            table.setRowCount(0)


    def _color_from_hex(self, hex_color: str):
        from PyQt5.QtGui import QColor, QBrush
        color = QColor(hex_color)
        return QBrush(color)
