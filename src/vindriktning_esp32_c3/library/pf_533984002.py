import faebryk.library._F as F
from faebryk.core.core import Module
from faebryk.libs.util import times


class pf_533984002(Module):
    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            pin = times(2, F.Electrical)
            # mount = times(2, Mechanical)
            mount = times(2, F.Electrical)

        self.IFs = _IFs(self)

        x = self.IFs
        self.add_trait(
            F.can_attach_to_footprint_via_pinmap(
                {
                    "1": x.pin[0],
                    "2": x.pin[1],
                    "3": x.mount[0],
                    "4": x.mount[1],
                }
            )
        )

        self.add_trait(F.has_designator_prefix_defined("J"))
