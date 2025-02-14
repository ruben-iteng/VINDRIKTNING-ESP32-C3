import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L


class FanConnector(Module):
    power: F.ElectricPower
    plug: F.pf_533984002

    def __preinit__(self):
        self.plug.pin[0].connect(self.power.lv)
        self.plug.pin[1].connect(self.power.hv)
        self.add(
            F.has_explicit_part.by_supplier(
                "C393945",
                pinmap={
                    "1": self.plug.pin[0],
                    "2": self.plug.pin[1],
                },
            )
        )
