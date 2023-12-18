from faebryk.core.core import Module
from faebryk.library.can_attach_to_footprint_via_pinmap import (
    can_attach_to_footprint_via_pinmap,
)
from faebryk.library.can_bridge_defined import can_bridge_defined
from faebryk.library.ElectricLogic import ElectricLogic
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.has_designator_prefix_defined import (
    has_designator_prefix_defined,
)
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

        x = self.IFs
        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "2": x.power.NODEs.lv,
                    "1": x.di.NODEs.signal,
                    "3": x.power.NODEs.hv,
                    "4": x.do.NODEs.signal,
                }
            )
        )

        # connect all logic references
        ref = ElectricLogic.connect_all_module_references(self)
        self.add_trait(has_single_electric_reference_defined(ref))

        self.add_trait(has_designator_prefix_defined("LED"))

        # Add bridge trait
        self.add_trait(can_bridge_defined(x.di, x.do))
