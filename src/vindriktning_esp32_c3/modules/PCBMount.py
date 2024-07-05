import faebryk.library._F as F
from faebryk.core.core import Module
from faebryk.libs.util import times
from vindriktning_esp32_c3.library.Mounting_Hole import Mounting_Hole


class PCB_Mount(Module):
    """
    Mounting holes and features for the PCB
    """

    def __init__(self, enabled: bool = True) -> None:
        super().__init__()

        class _IFs(Module.IFS()): ...

        self.IFs = _IFs(self)

        class _NODEs(Module.NODES()):
            screw_holes = times(3, lambda: Mounting_Hole(diameter=F.Constant(2.1)))

        self.NODEs = _NODEs(self)
