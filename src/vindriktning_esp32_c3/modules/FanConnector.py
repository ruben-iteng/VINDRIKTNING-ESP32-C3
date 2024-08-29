import faebryk.library._F as F
from faebryk.core.core import Module


class FanConnector(Module):
    def __preinit__(self):
        self.plug.pin[0].connect(self.power.lv)
        self.plug.pin[1].connect(self.power.hv)

    power: F.ElectricPower
    plug: F.pf_533984002
