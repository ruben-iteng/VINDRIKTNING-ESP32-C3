import faebryk.library._F as F
from faebryk.core.core import Module


class USBLC6_2P6(Module):
    """
    Low capacitance TVS diode array (for USB2.0)
    """

    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            usb = F.USB2_0()

        self.IFs = _IFs(self)

        x = self.IFs
        self.add_trait(
            F.can_attach_to_footprint_via_pinmap(
                {
                    "1": x.usb.IFs.d.IFs.p,
                    "2": x.usb.IFs.buspower.IFs.lv,
                    "3": x.usb.IFs.d.IFs.n,
                    "4": x.usb.IFs.d.IFs.n,
                    "5": x.usb.IFs.buspower.IFs.hv,
                    "6": x.usb.IFs.d.IFs.p,
                }
            )
        )

        self.add_trait(F.has_designator_prefix_defined("U"))

        self.add_trait(
            F.has_datasheet_defined(
                "https://datasheet.lcsc.com/lcsc/2108132230_TECH-PUBLIC-USBLC6-2P6_C2827693.pdf"
            )
        )
