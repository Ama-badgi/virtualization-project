from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, \
    QPushButton, QSizePolicy


class WarningDialogue(QWidget):
    def __init__(self, message: str) -> None:
        super().__init__()
        self.setMinimumSize(400, 200)
        self.setWindowTitle("Warning")
        self.mainLayout = QVBoxLayout()

        messageLayout = QVBoxLayout()
        text = QLabel(message)
        text.setAlignment(Qt.AlignCenter)

        button = QPushButton("Close")
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.clicked.connect(self.close)

        messageLayout.addWidget(text)
        messageLayout.addWidget(button)
        messageLayout.setAlignment(button, Qt.AlignHCenter)

        self.mainLayout.addLayout(messageLayout)
        self.setLayout(self.mainLayout)

        self.show()
