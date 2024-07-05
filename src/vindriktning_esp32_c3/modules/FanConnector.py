import faebryk.library._F as F
from faebryk.core.core import Module
from vindriktning_esp32_c3.library.pf_533984002 import pf_533984002


class FanConnector(Module):
    def __init__(self) -> None:
        super().__init__()

        class _IFs(Module.IFS()):
            power = F.ElectricPower()

        self.IFs = _IFs(self)

        class _NODEs(Module.NODES()):
            plug = pf_533984002()

        self.NODEs = _NODEs(self)

        self.NODEs.plug.IFs.pin[0].connect(self.IFs.power.IFs.lv)
        self.NODEs.plug.IFs.pin[1].connect(self.IFs.power.IFs.hv)
