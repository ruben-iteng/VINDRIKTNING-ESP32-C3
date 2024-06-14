import faebryk.library._F as F
from faebryk.core.core import Module


class Fan(Module):
    def __init__(self) -> None:
        super().__init__()

        class _IFs(Module.IFS()):
            power = F.ElectricPower()

        self.IFs = _IFs(self)

        # components
        class _NODEs(Module.NODES()):
            ...
            # TODO connector = some 2 pin thing

        self.NODEs = _NODEs(self)

        self.IFs.power.PARAMs.voltage.merge(F.Constant(5))
        # self.IFs.power.PARAMs.current_sink.merge(F.Constant(40 * m))
