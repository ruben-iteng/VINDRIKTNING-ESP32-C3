# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.core import Module, Parameter
from faebryk.core.util import unit_map
from faebryk.library.can_bridge_defined import can_bridge_defined
from faebryk.library.Constant import Constant
from faebryk.library.Electrical import Electrical
from faebryk.library.has_type_description import has_type_description
from faebryk.libs.util import times


class Inductor(Module):
    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        self._setup_traits()
        return self

    def __init__(self, inductance: Parameter):
        super().__init__()
        self._setup_interfaces()
        self.set_inductance(inductance)

    def _setup_traits(self):
        class _has_type_description(has_type_description.impl()):
            @staticmethod
            def get_type_description():
                assert isinstance(self.inductance, Constant)
                return unit_map(
                    self.inductance.value,
                    ["µH", "mH", "H", "kH", "MH", "GH"],
                    start="H",
                )

            def is_implemented(self):
                c = self.get_obj()
                assert isinstance(c, Inductor)
                return type(c.inductance) is Constant

        self.add_trait(_has_type_description())

    def _setup_interfaces(self):
        class _IFs(super().IFS()):
            unnamed = times(2, Electrical)

        self.IFs = _IFs(self)
        self.add_trait(can_bridge_defined(*self.IFs.unnamed))

    def set_inductance(self, inductance: Parameter):
        self.inductance = inductance

        if type(inductance) is not Constant:
            return
        _inductance: Constant = inductance

        class _has_type_description(has_type_description.impl()):
            @staticmethod
            def get_type_description():
                return unit_map(
                    _inductance.value, ["µH", "mH", "H", "kH", "MH", "GH"], start="H"
                )

        self.add_trait(_has_type_description())
