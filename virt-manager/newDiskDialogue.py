from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, \
    QLabel, QLineEdit, QCheckBox, QPushButton, QSizePolicy
from functools import partial


class NewDiskDialogue(QWidget):
    def __init__(self, parentWindow, domain) -> None:
        super().__init__()
        parentWindow.setEnabled(False)
        self.parentWindow = parentWindow
        self.info = None
        self.mainLayout = QVBoxLayout()
        
        nameLayout = QHBoxLayout()
        nameLayout.addWidget(QLabel("Name:"))
        self.nameTextField = QLineEdit()
        nameLayout.addWidget(self.nameTextField)

        sourceLayout = QHBoxLayout()
        sourceLayout.addWidget(QLabel("Source file:"))
        self.sourceTextField = QLineEdit()
        sourceLayout.addWidget(self.sourceTextField)

        readOnlyLayout = QHBoxLayout()
        readOnlyLayout.addWidget(QLabel("Make disk read-only"))
        self.readOnlyCheck = QCheckBox()
        readOnlyLayout.addWidget(self.readOnlyCheck)

        self.okButton = QPushButton("OK")
        self.okButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.okButton.clicked.connect(partial(self.parentWindow.addDisk,
                                              domain))

        self.mainLayout.addLayout(nameLayout)
        self.mainLayout.addLayout(sourceLayout)
        self.mainLayout.addLayout(readOnlyLayout)
        self.mainLayout.addWidget(self.okButton)

        self.setLayout(self.mainLayout)
        self.show()
        self.setFocus()

    def getInfo(self) -> None:
        if len(self.nameTextField.text()) == 0 \
                or self.nameTextField.text() in self.parentWindow.allDiskNames \
                    or len(self.nameTextField.text()) == 0:
            self.parentWindow.setEnabled(True)
            self.close()

        self.parentWindow.newDiskInfo = (self.nameTextField.text(),
                                         self.sourceTextField.text(),
                                         self.readOnlyCheck.isChecked())
        self.parentWindow.setEnabled(True)
        self.parentWindow.newDiskInfo = self.nameTextField.text(), \
        self.sourceTextField.text(), self.readOnlyCheck.isChecked()
        self.close()
