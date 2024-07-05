from faebryk.core.core import Module
from faebryk.library.can_attach_to_footprint_symmetrically import (
    can_attach_to_footprint_symmetrically,
)
from faebryk.library.Constant import Constant
from faebryk.library.Electrical import Electrical
from faebryk.library.has_defined_footprint import has_defined_footprint
from faebryk.library.has_designator_prefix_defined import (
    has_designator_prefix_defined,
)
from faebryk.library.KicadFootprint import KicadFootprint


class Mounting_Hole(Module):
    def __init__(self, diameter: Constant) -> None:
        super().__init__()
        self.diameter = diameter
        if self.diameter.value != 2.1:
            raise NotImplementedError(
                "Only 2.1mm diameter mounting holes are supported for now"
            )

        # interfaces
        class _IFs(Module.IFS()):
            pin = Electrical()

        self.IFs = _IFs(self)

        # TODO make a universal footprint
        self.add_trait(can_attach_to_footprint_symmetrically())
        self.add_trait(
            has_defined_footprint(
                KicadFootprint("MountingHole:MountingHole_2.1mm", pin_names=[])
            )
        )
        self.add_trait(has_designator_prefix_defined("H"))
