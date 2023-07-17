from faebryk.core.core import Module
from faebryk.library.can_attach_to_footprint_via_pinmap import (
    can_attach_to_footprint_via_pinmap,
)
from faebryk.library.Capacitor import Capacitor
from faebryk.library.ElectricLogic import ElectricLogic
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.has_defined_type_description import (
    has_defined_type_description,
)
from faebryk.library.I2C import I2C
from faebryk.library.Resistor import Resistor
from faebryk.library.TBD import TBD


class BH1750FVI_TR(Module):
    def __init__(self) -> None:
        super().__init__()

        class _NODEs(Module.NODES()):
            i2c_termination_resistors = [Resistor(TBD()) for _ in range(2)]
            decoupling_cap = Capacitor(TBD())

        self.NODEs = _NODEs(self)

        class _IFs(Module.IFS()):
            power = ElectricPower()
            addr = ElectricLogic()
            dvi = ElectricLogic()
            # TODO connect dvi to power.hv via 1K resistor and to power.lv via
            # 1uF capacitor as part of the reset circuit (dvi should be >=1uS
            # delay from power.hv is high)
            ep = ElectricLogic()
            i2c = I2C()

        self.IFs = _IFs(self)

        x = self.IFs
        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "1": x.power.NODEs.hv,
                    "2": x.addr.NODEs.signal,
                    "3": x.power.NODEs.lv,
                    "4": x.i2c.NODEs.sda.NODEs.signal,
                    "5": x.dvi.NODEs.signal,
                    "6": x.i2c.NODEs.scl.NODEs.signal,
                    "7": x.ep.NODEs.signal,
                }
            )
        )

        self.IFs.i2c.terminate(tuple(self.NODEs.i2c_termination_resistors))
        self.IFs.power.decouple(self.NODEs.decoupling_cap)

        self.add_trait(has_defined_type_description("U"))

    def set_address(self, addr: int):
        # ADDR = ‘H’ ( ADDR ≧ 0.7VCC ) “1011100“
        # ADDR = 'L' ( ADDR ≦ 0.3VCC ) “0100011“
        ...
        # assert addr < (1 << len(self.IFs.e))

        # for i, e in enumerate(self.IFs.e):
        #    e.set(addr & (1 << i) != 0)
