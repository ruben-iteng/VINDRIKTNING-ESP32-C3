import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L


class PM1006Connector(Module):
    """
    Connector with the PM1006 particulate matter sensor specific pinout.
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    plug: F.B4B_ZR_SM4_TF

    power: F.ElectricPower
    data: F.UART_Base

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    @L.rt_field
    def single_electric_reference(self):
        return F.has_single_electric_reference_defined(
            F.ElectricLogic.connect_all_module_references(self)
        )

    def __preinit__(self):
        # ------------------------------------
        #           connections
        # ------------------------------------
        self.plug.pin[3].connect(self.power.lv)
        self.plug.pin[2].connect(self.power.hv)
        self.plug.pin[1].connect(self.data.tx.line)  # connector out sensor in
        self.plug.pin[0].connect(self.data.rx.line)  # connector in sensor out

        # ------------------------------------
        #          parametrization
        # ------------------------------------
        self.plug.add(F.has_explicit_part.by_supplier("C145997"))
