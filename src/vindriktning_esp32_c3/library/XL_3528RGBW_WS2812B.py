import faebryk.libs.picker.lcsc as lcsc
from faebryk.core.core import Module
from faebryk.library.can_attach_to_footprint_via_pinmap import (
    can_attach_to_footprint_via_pinmap,
)
from faebryk.library.can_bridge_defined import can_bridge_defined
from faebryk.library.ElectricLogic import ElectricLogic
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.has_datasheet_defined import has_datasheet_defined
from faebryk.library.has_designator_prefix_defined import has_designator_prefix_defined
from faebryk.library.has_single_electric_reference_defined import (
    has_single_electric_reference_defined,
)


class XL_3528RGBW_WS2812B(Module):
    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power = ElectricPower()
            do = ElectricLogic()
            di = ElectricLogic()

        self.IFs = _IFs(self)

        # connect all logic references
        ref = ElectricLogic.connect_all_module_references(self)
        self.add_trait(has_single_electric_reference_defined(ref))

        self.add_trait(has_designator_prefix_defined("LED"))

        # Add bridge trait
        self.add_trait(can_bridge_defined(self.IFs.di, self.IFs.do))

        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "1": self.IFs.power.IFs.lv,
                    "2": self.IFs.di.IFs.signal,
                    "3": self.IFs.power.IFs.hv,
                    "4": self.IFs.do.IFs.signal,
                }
            )
        )

        lcsc.attach_footprint(self, "C2890364")

        self.add_trait(
            has_datasheet_defined(
                "https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2402181504_XINGLIGHT-XL-3528RGBW-WS2812B_C2890364.pdf"
            )
        )
