from faebryk.core.core import Module
from faebryk.library.can_attach_to_footprint_via_pinmap import (
    can_attach_to_footprint_via_pinmap,
)
from faebryk.library.Electrical import Electrical
from faebryk.library.has_designator_prefix_defined import (
    has_designator_prefix_defined,
)
from faebryk.libs.util import times


class B4B_ZR_SM4_TF(Module):
    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            pin = times(4, Electrical)
            # pad = times(2, Mechanical)
            mount = times(2, Electrical)

        self.IFs = _IFs(self)

        x = self.IFs
        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "1": x.pin[0],
                    "2": x.pin[1],
                    "3": x.pin[2],
                    "4": x.pin[3],
                    "5": x.mount[0],
                    "6": x.mount[1],
                }
            )
        )

        self.add_trait(has_designator_prefix_defined("J"))
