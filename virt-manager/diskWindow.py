from libvirt import virDomain, libvirtError, \
     VIR_DOMAIN_AFFECT_CONFIG, VIR_DOMAIN_AFFECT_LIVE
from libvirtUtils import DiskInfo, getALlDiskInfo, detachDisk, attachDisk
from warningDialogue import WarningDialogue
from newDiskDialogue import NewDiskDialogue
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, \
    QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QSizePolicy
from PyQt5.QtGui import QIcon
from functools import partial


class DiskGuiElement:
    def __init__(self, detachAttachButton: QPushButton,
                 nameField: QLabel) -> None:
        self.detachAttachButton = detachAttachButton
        self.nameField = nameField


class DiskWindow(QWidget):
    def __init__(self, domain: virDomain, parentWindow) -> None:
        super().__init__()
        self.newDiskInfo = None
        self.domain = domain
        self.parentWindow = parentWindow
        self.setWindowTitle(domain.name() + " disks")

        self.allDiskInfo = getALlDiskInfo(domain)
        self.allDiskNames: set[str] = set()
        self.allDiskGuiElements: list[DiskGuiElement] = []
        self.initUi()

    def initUi(self) -> None:
        self.setMinimumSize(250, 125)
        self.mainLayout = QVBoxLayout()

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)

        scrollContent = QWidget()
        self.scrollLayout = QVBoxLayout(scrollContent)

        seperationLine = QFrame()
        seperationLine.setFrameShape(QFrame.HLine)
        attachButton = QPushButton()
        attachButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        attachButton.setIcon(QIcon("resources/bootButton.png"))
        if not self.domain.isActive():
            attachButton.setEnabled(False)
        attachButton.clicked.connect(partial(self.makeDiskDialogue, self.domain))

        self.scrollLayout.addWidget(attachButton)
        self.scrollLayout.setAlignment(attachButton, Qt.AlignRight)
        self.scrollLayout.addWidget(seperationLine)

        self.diskLayout = QVBoxLayout()
        for diskInfo in self.allDiskInfo:
            self.allDiskNames.add(diskInfo.name)
            self.initDiskLayout(diskInfo)
        scrollContent.setLayout(self.scrollLayout)
        self.scrollArea.setWidget(scrollContent)

        self.mainLayout.addWidget(self.scrollArea)
        self.setLayout(self.mainLayout)
        self.show()
        self.setFocus()

    def initDiskLayout(self, diskInfo: DiskInfo) -> None:
        seperationLine = QFrame()
        seperationLine.setFrameShape(QFrame.HLine)
        diskInfoLayout = QHBoxLayout()

        detachButton = QPushButton()
        detachButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        detachButton.setIcon(QIcon("resources/shutdownButton.png"))
        if not self.domain.isActive():
            detachButton.setEnabled(False)
        nameField = QLabel(diskInfo.name)

        diskGuiElement = DiskGuiElement(detachButton, nameField)
        self.allDiskGuiElements.append(diskGuiElement)
        detachButton.clicked.connect(partial(self.removeDisk,
                                                   self.domain,
                                                   diskInfo))

        diskInfoLayout.addWidget(detachButton)
        diskInfoLayout.addWidget(nameField)

        self.diskLayout.addLayout(diskInfoLayout)
        self.diskLayout.addWidget(seperationLine)

        self.scrollLayout.addLayout(self.diskLayout)

    def removeDisk(self, domain: virDomain, diskInfo: DiskInfo) -> None:
        try:
            detachDisk(domain, diskInfo)
            self.allDiskNames.remove(diskInfo.name)
        except libvirtError as err:
            self.warning = WarningDialogue(err.get_error_message())
            self.close()
    
    def makeDiskDialogue(self, domain: virDomain) -> None:
        self.diskDialogue = NewDiskDialogue(self, domain)

    def addDisk(self, domain: virDomain) -> None:
        try:
            xml = None
            self.diskDialogue.getInfo()
            with open("resources/diskXMLTemplate.xml", 'r') as xmlTemplate:
                if self.newDiskInfo is None:
                    return
                diskName, sourcePath, isReadOnly = self.newDiskInfo
                featuresString = ""
                if isReadOnly:
                    featuresString = "<readonly/>"
                xml = xmlTemplate.read().format(sourcePath, diskName, featuresString)
            if xml is None:
                self.newDiskInfo = None
                return
            attachDisk(domain, xml)
            newDiskInfo = DiskInfo(diskName, xml)
            self.initDiskLayout(newDiskInfo)
            self.newDiskInfo = None
        except libvirtError as err:
            self.warning = WarningDialogue(err.get_error_message())
            self.newDiskInfo = None
            self.close()

    def closeEvent(self, event) -> None:
        self.parentWindow.setEnabled(True)
        self.parentWindow.setFocus()
        event.accept()
