import faebryk.libs.picker.lcsc as lcsc
from faebryk.core.core import Module
from faebryk.library.can_attach_to_footprint_via_pinmap import (
    can_attach_to_footprint_via_pinmap,
)
from faebryk.library.Electrical import Electrical
from faebryk.library.has_designator_prefix_defined import (
    has_designator_prefix_defined,
)
from faebryk.library.USB2_0 import USB2_0
from faebryk.libs.util import times


class USB_Type_C_Receptacle_14_pin_Vertical(Module):
    """
    14 pin vertical female USB Type-C connector
    918-418K2022Y40000
    """

    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            # TODO make arrays?
            cc1 = Electrical()
            cc2 = Electrical()
            shield = Electrical()
            # power
            gnd = times(4, Electrical)
            vbus = times(4, Electrical)
            # diffpairs: p, n
            usb = USB2_0()

        self.IFs = _IFs(self)

        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "1": self.IFs.gnd[0],
                    "2": self.IFs.vbus[0],
                    "3": self.IFs.usb.IFs.d.IFs.n,
                    "4": self.IFs.usb.IFs.d.IFs.p,
                    "5": self.IFs.cc2,
                    "6": self.IFs.vbus[1],
                    "7": self.IFs.gnd[1],
                    "8": self.IFs.gnd[2],
                    "9": self.IFs.vbus[2],
                    "10": self.IFs.usb.IFs.d.IFs.n,
                    "11": self.IFs.usb.IFs.d.IFs.p,
                    "12": self.IFs.cc1,
                    "13": self.IFs.vbus[3],
                    "14": self.IFs.gnd[3],
                    "0": self.IFs.shield,
                }
            )
        )

        lcsc.attach_footprint(self, "C168704")

        self.add_trait(has_designator_prefix_defined("x"))
