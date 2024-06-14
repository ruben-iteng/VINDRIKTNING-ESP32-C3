import faebryk.library._F as F
from faebryk.core.core import Module
from faebryk.core.util import connect_to_all_interfaces


class ME6211C33M5G_N(Module):
    """
    3.3V 600mA LDO
    https://datasheet.lcsc.com/lcsc/1811131510_MICRONE-Nanjing-Micro-One-Elec-ME6211C33M5G-N_C82942.pdf

    """

    def __init__(self, default_enabled: bool = True) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power_in = F.ElectricPower()
            power_out = F.ElectricPower()
            enable = F.Electrical()

        self.IFs = _IFs(self)

        # components
        class _NODEs(Module.NODES()): ...

        self.NODEs = _NODEs(self)

        # set constraints
        self.IFs.power_out.PARAMs.voltage.merge(F.Range(3.3 * 0.98, 3.3 * 1.02))

        # connect decouple capacitor
        self.IFs.power_in.get_trait(F.can_be_decoupled).decouple()
        self.IFs.power_out.get_trait(F.can_be_decoupled).decouple()
        # TODO: should be 1uF

        # LDO in & out share gnd reference
        self.IFs.power_in.IFs.lv.connect(self.IFs.power_out.IFs.lv)

        self.add_trait(F.has_designator_prefix_defined("U"))
        self.add_trait(
            F.can_attach_to_footprint_via_pinmap(
                {
                    "1": self.IFs.power_in.IFs.hv,
                    "2": self.IFs.power_in.IFs.lv,
                    "3": self.IFs.enable,
                    "5": self.IFs.power_out.IFs.hv,
                }
            )
        )

        if default_enabled:
            self.IFs.enable.connect(self.IFs.power_in.IFs.hv)

        connect_to_all_interfaces(self.IFs.power_in.IFs.lv, [self.IFs.power_out.IFs.lv])
