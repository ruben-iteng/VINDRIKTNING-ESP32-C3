import faebryk.library._F as F
from faebryk.core.core import Module


class PM1006Connector(Module):
    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power = F.ElectricPower()
            data = F.UART_Base()

        self.IFs = _IFs(self)

        # components
        class _NODEs(Module.NODES()):
            plug = F.B4B_ZR_SM4_TF()

        self.NODEs = _NODEs(self)

        self.NODEs.plug.IFs.pin[3].connect(self.IFs.power.IFs.lv)
        self.NODEs.plug.IFs.pin[2].connect(self.IFs.power.IFs.hv)
        self.NODEs.plug.IFs.pin[1].connect(
            self.IFs.data.IFs.tx.IFs.signal
        )  # connector out sensor in
        self.NODEs.plug.IFs.pin[0].connect(
            self.IFs.data.IFs.rx.IFs.signal
        )  # connector in sensor out

        ref = F.ElectricLogic.connect_all_module_references(self)
        self.add_trait(F.has_single_electric_reference_defined(ref))
