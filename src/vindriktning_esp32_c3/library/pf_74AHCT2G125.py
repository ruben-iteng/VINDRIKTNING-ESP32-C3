from faebryk.core.core import Module
from faebryk.library.can_attach_to_footprint_via_pinmap import (
    can_attach_to_footprint_via_pinmap,
)
from faebryk.library.ElectricLogic import ElectricLogic
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.has_defined_type_description import (
    has_defined_type_description,
)


class pf_74AHCT2G125(Module):
    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power = ElectricPower()
            a = ElectricLogic()
            y = ElectricLogic()
            oe = ElectricLogic()

        self.IFs = _IFs(self)

        x = self.IFs
        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "1": x.oe.NODEs.signal,
                    "2": x.a.NODEs.signal,
                    "3": x.power.NODEs.lv,
                    "4": x.y.NODEs.signal,
                    "5": x.power.NODEs.hv,
                }
            )
        )

        self.add_trait(has_defined_type_description("U"))
