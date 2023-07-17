from faebryk.core.core import Module
from faebryk.library.can_attach_to_footprint_via_pinmap import (
    can_attach_to_footprint_via_pinmap,
)
from faebryk.library.ElectricLogic import ElectricLogic
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.has_defined_type_description import (
    has_defined_type_description,
)


class SK9822_EC20(Module):
    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power = ElectricPower()
            sdo = ElectricLogic()
            sdi = ElectricLogic()
            cko = ElectricLogic()
            ckl = ElectricLogic()

        self.IFs = _IFs(self)

        x = self.IFs
        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "1": x.sdo.NODEs.signal,
                    "2": x.power.NODEs.lv,
                    "3": x.sdi.NODEs.signal,
                    "4": x.ckl.NODEs.signal,
                    "5": x.power.NODEs.hv,
                    "6": x.cko.NODEs.signal,
                }
            )
        )

        self.add_trait(has_defined_type_description("LED"))
