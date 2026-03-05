from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QPushButton, QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
import os

class LoginView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hiandco Tech ERP - Giriş")
        self.setFixedSize(420, 520)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._center_on_screen()

        self.on_login_success = None
        self._drag_pos = None

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
        container.setObjectName("loginContainer")
        container.setStyleSheet("""
            QWidget#loginContainer {
                background-color: #1a1a2e;
                border-radius: 16px;
                border: 2px solid #0f3460;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(40, 30, 40, 30)
        container_layout.setSpacing(12)
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #a6a6a6;
                border: none;
                font-size: 16px;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
                color: white;
            }
        """)
        close_btn.clicked.connect(self.close)
        close_layout.addWidget(close_btn)
        container_layout.addLayout(close_layout)
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        logo_path = os.path.join(os.environ.get('HIANDCO_BASE_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled)
        else:
            logo_label.setText("🔑")
            logo_label.setStyleSheet("font-size: 48px;")
        container_layout.addWidget(logo_label)
        title = QLabel("Giriş Yap")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")
        container_layout.addWidget(title)

        subtitle = QLabel("Devam etmek için giriş yapın")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #a6a6a6; font-size: 12px;")
        container_layout.addWidget(subtitle)
        container_layout.addSpacing(15)
        username_label = QLabel("Kullanıcı Adı")
        username_label.setStyleSheet("color: #a6a6a6; font-size: 12px; font-weight: bold;")
        container_layout.addWidget(username_label)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Kullanıcı adınızı girin")
        self.username_input.setFixedHeight(42)
        self.username_input.setStyleSheet(self._input_style())
        container_layout.addWidget(self.username_input)

        container_layout.addSpacing(5)

        password_label = QLabel("Şifre")
        password_label.setStyleSheet("color: #a6a6a6; font-size: 12px; font-weight: bold;")
        container_layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Şifrenizi girin")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(42)
        self.password_input.setStyleSheet(self._input_style())
        self.password_input.returnPressed.connect(self._handle_login)
        container_layout.addWidget(self.password_input)

        container_layout.addSpacing(5)

        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet("color: #ff6b6b; font-size: 12px;")
        self.error_label.setVisible(False)
        container_layout.addWidget(self.error_label)

        container_layout.addSpacing(10)

        login_btn = QPushButton("Giriş Yap")
        login_btn.setFixedHeight(44)
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.setFont(QFont("Segoe UI", 13, QFont.Bold))
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #e94560;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ff6b81;
            }
            QPushButton:pressed {
                background-color: #c23152;
            }
        """)
        login_btn.clicked.connect(self._handle_login)
        container_layout.addWidget(login_btn)

        container_layout.addStretch()

        footer = QLabel("© 2026 BarcodeProgramma")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #6c7293; font-size: 10px;")
        container_layout.addWidget(footer)

        layout.addWidget(container)

    def _input_style(self) -> str:
        return """
            QLineEdit {
                background-color: #16213e;
                color: #ffffff;
                border: 1px solid #2a2a4a;
                border-radius: 8px;
                padding: 0 15px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #e94560;
            }
            QLineEdit::placeholder {
                color: #6c7293;
            }
        """

    def _handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            self._show_error("Kullanıcı adı ve şifre boş bırakılamaz")
            return

        from controllers.auth_controller import AuthController
        auth = AuthController()
        result = auth.login(username, password)

        if result["success"]:
            self.error_label.setVisible(False)
            if self.on_login_success:
                self.on_login_success(result)
        else:
            self._show_error(result["message"])

    def _show_error(self, message: str):
        self.error_label.setText(message)
        self.error_label.setVisible(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.pos()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None