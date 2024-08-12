from warningDialogue import WarningDialogue
from mainWindow import MainWindow
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, \
    QPushButton, QSizePolicy, QLabel


class LaunchWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(400, 100)
        self.setWindowTitle("Launch Window")
        self.mainLayout = QVBoxLayout()

        inputLayout = QVBoxLayout()
        inputLayout.setSpacing(0)

        self.textField = QLineEdit()
        label = QLabel("Connection URI:")
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        inputLayout.addWidget(label)
        inputLayout.addWidget(self.textField)
        inputLayout.setAlignment(label, Qt.AlignCenter)
        inputLayout.setAlignment(self.textField, Qt.AlignVCenter)

        launchButton = QPushButton("Launch")
        launchButton.setSizePolicy(QSizePolicy.Fixed,
                                   QSizePolicy.Fixed)
        launchButton.clicked.connect(self.launchMainWindow)

        self.mainLayout.addLayout(inputLayout)
        self.mainLayout.addWidget(launchButton)
        self.mainLayout.setAlignment(launchButton, Qt.AlignHCenter)
        self.setLayout(self.mainLayout)
        self.show()

    def launchMainWindow(self) -> None:
        inputText = self.textField.text()
        if len(inputText) != 0:
            self.mainWindow = MainWindow(self.textField.text())
            self.close()
        else:
            self.warning = WarningDialogue("Connection URI can't be blank.")
