from launchWindow import LaunchWindow
import sys
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    launchWindow = LaunchWindow()
    sys.exit(app.exec_())
