from libvirt import VIR_DOMAIN_RUNNING, VIR_DOMAIN_BLOCKED, \
    VIR_DOMAIN_PAUSED, VIR_DOMAIN_SHUTDOWN, VIR_DOMAIN_SHUTOFF, \
    VIR_DOMAIN_CRASHED, VIR_DOMAIN_PMSUSPENDED, \
    VIR_DOMAIN_AFFECT_CONFIG, VIR_DOMAIN_AFFECT_LIVE, \
    virConnect, virDomain, libvirtError
from xml.etree.ElementTree import fromstring, tostring


class DomainInfo:
    def __init__(self, domain: virDomain) -> None:
        self.domain = domain

    def stateToString(self, state: int) -> str:
        if state == VIR_DOMAIN_RUNNING:
            return "Running"
        if state == VIR_DOMAIN_BLOCKED:
            return "Resource Blocked"
        if state == VIR_DOMAIN_PAUSED:
            return "Paused"
        if state == VIR_DOMAIN_SHUTDOWN:
            return "Shutting Down"
        if state == VIR_DOMAIN_SHUTOFF:
            return "Shut off"
        if state == VIR_DOMAIN_CRASHED:
            return "Crashed"
        if state == VIR_DOMAIN_PMSUSPENDED:
            return "Suspended by PM"

    def toString(self) -> str:
        state, maxMemory, memory, vcpuCount, cpuTime = self.domain.info()
        return """
        State: {}
        Memory: {}/{}KB
        Number of vCPUs: {}
        Cpu Time: {}ns""".format(self.stateToString(state), memory, maxMemory,
                                 vcpuCount, cpuTime)


class DiskInfo:
    def __init__(self, name, xml) -> None:
        self.name = name
        self.xml = xml


def getAllDomainInfo(conn: virConnect) -> list[DomainInfo]:
    domains: list[virDomain] = conn.listAllDomains()
    return [DomainInfo(domain) for domain in domains]


def getALlDiskInfo(domain: virDomain) -> list[DiskInfo]:
    allDiskInfo = []
    domainTree = fromstring(domain.XMLDesc())
    diskNames = [disk.attrib['dev'] for disk in domainTree.findall(".//disk[@device='disk']/target")]
    for name in diskNames:
        diskXml = tostring(domainTree
            .find(
            ".//disk[@device='disk']/target[@dev='{}']/..".format(name)),
            encoding="unicode")
        allDiskInfo.append(DiskInfo(name, diskXml))
    return allDiskInfo


def bootDomain(domain: virDomain) -> None:
    try:
        if not domain.isActive():
            domain.create()
    except Exception:
        return


def shutdownDomain(domain: virDomain) -> None:
    if domain.isActive():
        domain.shutdown()


def suspendDomain(domain: virDomain) -> None:
    if domain.isActive():
        domain.suspend()


def resumeDomain(domain: virDomain) -> None:
    if domain.info()[0] != VIR_DOMAIN_PAUSED:
        return
    domain.resume()


def forceShutDown(domain: virDomain) -> None:
    if domain.isActive():
        domain.destroy()


def destroyDomain(domain: virDomain) -> None:
    try:
        forceShutDown(domain)
        domain.undefine()
    except libvirtError:
        return


def detachDisk(domain: virDomain, diskInfo: DiskInfo) -> None:
    domain.detachDeviceFlags(diskInfo.xml, VIR_DOMAIN_AFFECT_LIVE | VIR_DOMAIN_AFFECT_CONFIG)


def attachDisk(domain: virDomain, xml: str) -> None:
    domain.attachDeviceFlags(xml, VIR_DOMAIN_AFFECT_LIVE | VIR_DOMAIN_AFFECT_CONFIG)
