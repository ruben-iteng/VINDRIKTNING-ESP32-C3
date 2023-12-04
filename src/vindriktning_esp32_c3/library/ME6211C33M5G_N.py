from faebryk.core.core import Module
from faebryk.core.util import connect_to_all_interfaces
from faebryk.library.can_attach_to_footprint_via_pinmap import (
    can_attach_to_footprint_via_pinmap,
)
from faebryk.library.Capacitor import Capacitor
from faebryk.library.Constant import Constant
from faebryk.library.Electrical import Electrical
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.has_defined_type_description import has_defined_type_description
from faebryk.libs.units import u
from faebryk.libs.util import times


class ME6211C33M5G_N(Module):
    """
    3.3V 600mA LDO
    https://datasheet.lcsc.com/lcsc/1811131510_MICRONE-Nanjing-Micro-One-Elec-ME6211C33M5G-N_C82942.pdf

    """

    def __init__(self, default_enabled: bool = True) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power_in = ElectricPower()
            power_out = ElectricPower()
            enable = Electrical()

        self.IFs = _IFs(self)

        # components
        class _NODEs(Module.NODES()):
            decoupling_caps = times(2, lambda: Capacitor(Constant(1 * u)))

        self.NODEs = _NODEs(self)

        # connect decouple capacitor
        self.IFs.power_in.decouple(self.NODEs.decoupling_caps[0])
        self.IFs.power_out.decouple(self.NODEs.decoupling_caps[1])

        # LDO in & out share gnd reference
        self.IFs.power_in.NODEs.lv.connect(self.IFs.power_out.NODEs.lv)

        self.add_trait(has_defined_type_description("U"))
        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "1": self.IFs.power_in.NODEs.hv,
                    "2": self.IFs.power_in.NODEs.lv,
                    "3": self.IFs.enable,
                    "5": self.IFs.power_out.NODEs.hv,
                }
            )
        )

        if default_enabled:
            self.IFs.enable.connect(self.IFs.power_in.NODEs.hv)

        connect_to_all_interfaces(
            self.IFs.power_in.NODEs.lv, [self.IFs.power_out.NODEs.lv]
        )
