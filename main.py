import sys
import os

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
    APP_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    APP_DIR = BASE_DIR

sys.path.insert(0, BASE_DIR)
os.environ['HIANDCO_BASE_DIR'] = BASE_DIR
os.environ['HIANDCO_APP_DIR'] = APP_DIR

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    icon_path = os.path.join(BASE_DIR, "assets", "favicon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    from views.splash_screen import SplashScreen
    splash = SplashScreen()

    def on_splash_finished():
        from views.login_view import LoginView
        login = LoginView()

        def on_login_success(result: dict):
            login.close()
            from views.main_window import MainWindow
            window = MainWindow(result.get("user", {}))
            window.show()
            app._main_window = window

        login.on_login_success = on_login_success
        login.show()
        app._login = login

    splash.on_finished = on_splash_finished
    splash.show()
    splash.start()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
