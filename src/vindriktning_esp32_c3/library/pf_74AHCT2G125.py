import faebryk.library._F as F
from faebryk.core.core import Module


class pf_74AHCT2G125(Module):
    """
    The 74AHC1G/AHCT1G125 is a high-speed Si-gate CMOS device.
    The 74AHC1G/AHCT1G125 provides one non-inverting buffer/line
    driver with 3-state output. The 3-state output is controlled
    by the output enable input (OE). A HIGH at OE causes the
    output to assume a high-impedance OFF-state.
    """

    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power = F.ElectricPower()
            a = F.ElectricLogic()
            y = F.ElectricLogic()
            oe = F.ElectricLogic()

        self.IFs = _IFs(self)

        x = self.IFs
        self.add_trait(
            F.can_attach_to_footprint_via_pinmap(
                {
                    "1": x.oe.IFs.signal,
                    "2": x.a.IFs.signal,
                    "3": x.power.IFs.lv,
                    "4": x.y.IFs.signal,
                    "5": x.power.IFs.hv,
                }
            )
        )

        # connect all logic references
        ref = F.ElectricLogic.connect_all_module_references(self)
        self.add_trait(F.has_single_electric_reference_defined(ref))

        self.add_trait(F.has_designator_prefix_defined("U"))

        self.add_trait(
            F.has_datasheet_defined(
                "https://datasheet.lcsc.com/lcsc/2304140030_Nexperia-74AHCT1G125GV-125_C12494.pdf"
            )
        )
