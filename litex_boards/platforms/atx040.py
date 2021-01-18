from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform
from litex.build.xilinx.programmer import XC3SProg

# IOs ----------------------------------------------------------------------------------------------

_io = [
    # Clk / Rst
    ("clk24", 0, Pins("J16"), IOStandard("LVCMOS33")),

    ("rst_n", 0, Pins("K15"), IOStandard("LVCMOS33")),
    ("rst_pu", 0, Pins("L16"), IOStandard("LVCMOS33")),

    # Serial
    ("serial", 0,
        Subsignal("tx", Pins("J1"), IOStandard("LVCMOS33")),
        Subsignal("rx", Pins("H1"), IOStandard("LVCMOS33"))
    ),

    # SDR SDRAM
    ("sdram_clock", 0, Pins("B1"), IOStandard("LVCMOS33"), Misc("SLEW=FAST")),
    ("sdram", 0,
        Subsignal("a", Pins(
            "N3 P1 P2 R1 C3 C1 C2 D1 E2 E1 N1 F3 F1")),
        Subsignal("dq", Pins(
            "H2 K5 J3 L3 L5 L4 M4 N4",
            "E3 D3 E4 F4 F5 G5 H4 J4")),
        Subsignal("we_n",  Pins("K1")),
        Subsignal("ras_n", Pins("L1")),
        Subsignal("cas_n", Pins("K2")),
        Subsignal("cs_n",  Pins("M3")),
        Subsignal("cke",   Pins("F2")),
        Subsignal("ba",    Pins("M1 M2")),
        Subsignal("dm",    Pins("K3 G1")),
        Misc("SLEW=FAST"),
        IOStandard("LVCMOS33"),
    ),

    ("cpu_bclk", 0, Pins("F16"), IOStandard("LVCMOS33")),
    ("cpu_pclk", 0, Pins("F14"), IOStandard("LVCMOS33")),

    ("mc68040", 0,

        Subsignal("cpu_ad", Pins(
            "C6  D6  E6  C7  C8  D5  B15 A14",
            "B14 A13 C13 A12 B12 A11 A10 A9",
            "C11 C9  B10 B8  A6  B5  B6  A8",
            "B3  A7  A3  C5  B2  A5  A4  A2")),
        Subsignal("cpu_dir", Pins("D8")),
        Subsignal("cpu_oe", Pins("D9")),

        Subsignal("cpu_siz", Pins("C10 D11")),
        Subsignal("cpu_tt", Pins("B16 C16")),

        Subsignal("cpu_rsto", Pins("C15")),
        Subsignal("cpu_tip", Pins("D12")),
        Subsignal("cpu_ts", Pins("E11")),
        Subsignal("cpu_rw", Pins("E8")),

        Subsignal("cpu_cdis", Pins("E15")),
        Subsignal("cpu_rsti", Pins("E16")),
        Subsignal("cpu_irq", Pins("D16")),
        Subsignal("cpu_ta", Pins("D14")),
        IOStandard("LVCMOS33"),
    ),
]

# Platform -----------------------------------------------------------------------------------------

class Platform(XilinxPlatform):
    default_clk_name   = "clk24"
    default_clk_period = 1e9/24e6

    def __init__(self, device="xc6slx16"):
        XilinxPlatform.__init__(self, device+"-2-ftg256", _io)

    def create_programmer(self):
        return XC3SProg(cable="xpc")

    def do_finalize(self, fragment):
        self.add_period_constraint(self.lookup_request("clk24", loose=True), 1e9/24e6)
        XilinxPlatform.do_finalize(self, fragment)
