import libvirt
from libvirtUtils import DomainInfo, getAllDomainInfo, bootDomain, \
    shutdownDomain, resumeDomain, suspendDomain, \
    destroyDomain, forceShutDown
from warningDialogue import WarningDialogue
from diskWindow import DiskWindow
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout,  \
    QLabel, QFrame, QSizePolicy, QScrollArea, QPushButton
from PyQt5.QtGui import QIcon
from functools import partial

DOMAIN_NOT_FOUND_ERROR_CODE = 42


class DomainGuiElement:
    def __init__(self, domain,
                 nameField: QLabel, stateField: QLabel,
                 suspendResumeButton: QPushButton,
                 shutdownBootButton: QPushButton,
                 forceShutdownButton: QPushButton,
                 destroyButton: QPushButton) -> None:
        self.domain = domain
        self.nameField = nameField
        self.stateField = stateField
        self.suspendResumeButton = suspendResumeButton
        self.shutdownBootButton = shutdownBootButton
        self.forceShutdownButton = forceShutdownButton
        self.destroyButton = destroyButton

        self.forceShutdownButton.setSizePolicy(QSizePolicy.Fixed,
                                               QSizePolicy.Fixed)
        self.forceShutdownButton.setIcon(QIcon(
            "resources/forceShutdownButton.png"))
        self.forceShutdownButton.clicked.connect(partial(forceShutDown,
                                                         self.domain))
        self.srButtonConnected = False
        self.sbButtonConnected = False
        self.updateSuspendResume()
        self.updateShutdownBoot()
        self.updateForceShutdown()

    def update(self, domainInfo, window) -> None:
        self.updateName()
        self.updateState(domainInfo)
        self.updateSuspendResume()
        self.updateShutdownBoot()
        self.updateForceShutdown()

    def updateSuspendResume(self) -> None:
        state = self.domain.info()[0]
        self.suspendResumeButton.setIcon(QIcon("resources/pauseButton.png"))
        if state in {libvirt.VIR_DOMAIN_SHUTDOWN,
                     libvirt.VIR_DOMAIN_PMSUSPENDED,
                     libvirt.VIR_DOMAIN_CRASHED,
                     libvirt.VIR_DOMAIN_SHUTOFF,
                     libvirt.VIR_DOMAIN_BLOCKED}:
            self.suspendResumeButton.setEnabled(False)
            return

        self.suspendResumeButton.setEnabled(True)
        if state == libvirt.VIR_DOMAIN_PAUSED:
            self.suspendResumeButton.setIcon(QIcon(
                "resources/resumeButton.png"))
            if self.srButtonConnected:
                self.suspendResumeButton.clicked.disconnect()
            self.suspendResumeButton.clicked.connect(partial(resumeDomain,
                                                             self.domain))
            self.srButtonConnected = True
        else:
            if self.srButtonConnected:
                self.suspendResumeButton.clicked.disconnect()
            self.suspendResumeButton.clicked.connect(partial(suspendDomain,
                                                             self.domain))
            self.srButtonConnected = True

    def updateShutdownBoot(self):
        state = self.domain.info()[0]
        self.shutdownBootButton.setIcon(QIcon("resources/shutdownButton.png"))
        if state in {libvirt.VIR_DOMAIN_SHUTDOWN,
                     libvirt.VIR_DOMAIN_PAUSED,
                     libvirt.VIR_DOMAIN_PMSUSPENDED,
                     libvirt.VIR_DOMAIN_CRASHED,
                     libvirt.VIR_DOMAIN_BLOCKED}:
            self.shutdownBootButton.setEnabled(False)
            return

        self.shutdownBootButton.setEnabled(True)
        if state == libvirt.VIR_DOMAIN_SHUTOFF:
            self.shutdownBootButton.setIcon(QIcon("resources/bootButton.png"))
            if self.sbButtonConnected:
                self.shutdownBootButton.clicked.disconnect()
            self.shutdownBootButton.clicked.connect(partial(bootDomain,
                                                            self.domain))
            self.sbButtonConnected = True
        else:
            if self.sbButtonConnected:
                self.shutdownBootButton.clicked.disconnect()
            self.shutdownBootButton.clicked.connect(partial(shutdownDomain,
                                                            self.domain))
            self.sbButtonConnected = True

    def updateForceShutdown(self):
        state = self.domain.info()[0]
        self.forceShutdownButton.setEnabled(False)
        if state == libvirt.VIR_DOMAIN_RUNNING:
            self.forceShutdownButton.setEnabled(True)

    def updateName(self):
        self.nameField.setText(self.domain.name())

    def updateState(self, domainInfo: DomainInfo):
        self.stateField.setText(domainInfo.toString())


class MainWindow(QWidget):
    def __init__(self, connUri: str) -> None:
        super().__init__()
        try:
            self.conn = libvirt.open(connUri)

            self.allDomainInfo = getAllDomainInfo(self.conn)
            self.domainIdSet = set()
            self.allDomainGuiElements: list[DomainGuiElement] = []
            self.initUi()

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update)
            self.timer.start(1000)
        except libvirt.libvirtError as err:
            self.warning = WarningDialogue(err.get_error_message())
            self.conn.close()
            self.close()

    def initUi(self) -> None:
        self.setMinimumSize(485, 160)
        self.setWindowTitle("VirtManager")
        self.mainLayout = QVBoxLayout()

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)

        scrollContent = QWidget()
        self.scrollLayout = QVBoxLayout(scrollContent)

        for domainInfo in self.allDomainInfo:
            self.initDomainLayout(domainInfo)
        scrollContent.setLayout(self.scrollLayout)
        self.scrollArea.setWidget(scrollContent)

        self.mainLayout.addWidget(self.scrollArea)
        self.setLayout(self.mainLayout)
        self.show()

    def initDomainLayout(self, domainInfo: DomainInfo) -> None:
        self.domainIdSet.add(domainInfo.domain.ID())

        seperationLine = QFrame()
        seperationLine.setFrameShape(QFrame.HLine)

        self.vmLayout = QVBoxLayout()
        nameField = QLabel(domainInfo.domain.name())
        stateField = QLabel(domainInfo.toString())

        self.vmLayout.addWidget(nameField)
        self.vmLayout.setAlignment(nameField, Qt.AlignCenter)
        self.initDomainInfoLayout(stateField, nameField, domainInfo)
        self.vmLayout.addWidget(seperationLine)

        self.scrollLayout.addLayout(self.vmLayout)
        self.scrollLayout.setAlignment(self.vmLayout, Qt.AlignVCenter)

    def initDomainInfoLayout(self, stateField: QLabel, nameField: QLabel,
                             domainInfo: DomainInfo) -> None:
        domainInfoLayout = QHBoxLayout()

        suspendResumeButton = QPushButton()
        suspendResumeButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        shutdownBootButton = QPushButton()
        shutdownBootButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        forceShutdownButton = QPushButton()

        destroyButton = QPushButton()
        destroyButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        destroyButton.setIcon(QIcon("resources/destroyButton.png"))
        domainInfoLayout.addWidget(destroyButton)
        domainInfoLayout.setAlignment(destroyButton, Qt.AlignRight)

        disksButton = QPushButton()
        disksButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        disksButton.setText("Disks")
        disksButton.clicked.connect(partial(self.openDiskWindow,
                                            domainInfo.domain))

        domainGuiElement = DomainGuiElement(domainInfo.domain,
                                            nameField, stateField,
                                            suspendResumeButton,
                                            shutdownBootButton,
                                            forceShutdownButton,
                                            destroyButton)
        destroyButton.clicked.connect(partial(self.removeDomain,
                                              domainInfo,
                                              domainGuiElement))
        self.allDomainGuiElements.append(domainGuiElement)

        domainInfoLayout.addWidget(stateField)
        domainInfoLayout.addWidget(suspendResumeButton)
        domainInfoLayout.addWidget(shutdownBootButton)
        domainInfoLayout.addWidget(forceShutdownButton)
        domainInfoLayout.addWidget(disksButton)

        domainInfoLayout.setAlignment(stateField, Qt.AlignLeft)
        domainInfoLayout.setAlignment(suspendResumeButton, Qt.AlignRight)
        domainInfoLayout.setAlignment(shutdownBootButton, Qt.AlignRight)
        domainInfoLayout.setAlignment(forceShutdownButton, Qt.AlignRight)
        domainInfoLayout.addStretch()

        self.vmLayout.addLayout(domainInfoLayout)
        self.vmLayout.setAlignment(domainInfoLayout, Qt.AlignCenter)

    def removeDomain(self, domainInfo: DomainInfo,
                     domainGuiElement: DomainGuiElement) -> None:
        destroyDomain(domainInfo.domain)
        self.domainIdSet.remove(domainInfo.domain.ID())
        self.allDomainGuiElements.remove(domainGuiElement)
        self.allDomainInfo.remove(domainInfo)
        self.removeItemsFromLayout(self.vmLayout)
        self.scrollLayout.removeItem(self.vmLayout)

    def removeItemsFromLayout(self, layout: QVBoxLayout | QHBoxLayout) -> None:
        while layout.count() != 0:
            item = layout.takeAt(0)
            layoutItem = item.layout()
            if layoutItem is not None:
                self.removeItemsFromLayout(layoutItem)
            else:
                widget = item.widget()
                if widget is not None:
                    layout.removeItem(item)
                    item.widget().deleteLater()

    def update(self):
        try:
            updatedDomains = self.conn.listAllDomains()
            if len(updatedDomains) > len(self.allDomainInfo):
                for domain in updatedDomains:
                    if domain.ID() not in self.domainIdSet:
                        domainInfo = DomainInfo(domain)
                        self.allDomainInfo.append(domainInfo)
                        self.domainIdSet.add(domain.ID())
                        self.initDomainLayout(domainInfo)
        except libvirt.libvirtError as err:
            self.warning = WarningDialogue(err.get_error_message())
            self.close()
            self.timer.timeout.disconnect()
        for idx, domainGuiElement in enumerate(self.allDomainGuiElements):
            try:
                domainGuiElement.update(self.allDomainInfo[idx], self)
            except libvirt.libvirtError as err:
                if err.get_error_code() == DOMAIN_NOT_FOUND_ERROR_CODE:
                    self.removeDomain(self.allDomainInfo[idx],
                                      domainGuiElement)
                else:
                    self.warning = WarningDialogue(err.get_error_message())
                    self.close()

    def openDiskWindow(self, domain) -> None:
        self.setEnabled(False)
        self.diskWindow = DiskWindow(domain, self)

    def closeEvent(self, event):
        if self.conn is not None:
            self.conn.close()
        event.accept()
