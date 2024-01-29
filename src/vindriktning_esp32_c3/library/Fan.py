from faebryk.core.core import Module
from faebryk.library.Constant import Constant
from faebryk.library.ElectricPower import ElectricPower


class Fan(Module):
    def __init__(self) -> None:
        super().__init__()

        class _IFs(Module.IFS()):
            power = ElectricPower()

        self.IFs = _IFs(self)

        # components
        class _NODEs(Module.NODES()):
            ...
            # TODO connector = some 2 pin thing

        self.NODEs = _NODEs(self)

        self.IFs.power.PARAMs.voltage.merge(Constant(5))
        # self.IFs.power.PARAMs.current_sink.merge(Constant(40 * m))
