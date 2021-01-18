#!/usr/bin/env python3

import os
import argparse
from fractions import Fraction

from migen import *

from litex.build.io import DDROutput

from litex_boards.platforms import atx040

from litex.soc.cores.clock import S6PLL
from litex.soc.integration.soc_core import *
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *

from litedram.modules import MT48LC16M16
from litedram.phy import GENSDRPHY, HalfRateGENSDRPHY

from migen.genlib.resetsync import AsyncResetSynchronizer

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform, sys_clk_freq):
        self.rst = Signal()
        self.clock_domains.cd_sys    = ClockDomain()
        self.clock_domains.cd_sys_ps = ClockDomain(reset_less=True)
        self.clock_domains.cd_bclk   = ClockDomain(reset_less=True)
        self.clock_domains.cd_pclk   = ClockDomain(reset_less=True)
        self.clock_domains.cd_clkin  = ClockDomain(reset_less=True)

        # # #

        ref_clk_freq = int(24e6)

        # Clk / Rst
        clk24 = platform.request("clk24")

        rst_n = platform.request("rst_n")

        rst_cnt = Signal(max=ref_clk_freq)
        rst_trg = Signal()

        self.sync.clkin += If(rst_cnt < int(ref_clk_freq), rst_cnt.eq(rst_cnt+1))

        self.comb += rst_trg.eq((rst_cnt > int(0.1*ref_clk_freq)) & (rst_cnt < int(0.2*ref_clk_freq)))

        # PLL
        self.submodules.pll = pll = S6PLL(speedgrade=-1)
        self.comb += pll.reset.eq(self.rst | ~rst_n | rst_trg)
        pll.register_clkin(clk24, ref_clk_freq)
        pll.create_clkout(self.cd_sys, sys_clk_freq)
        pll.create_clkout(self.cd_bclk, int(sys_clk_freq/4))
        pll.create_clkout(self.cd_pclk, int(sys_clk_freq/2))
        pll.create_clkout(self.cd_sys_ps, sys_clk_freq, phase=90)
        platform.add_false_path_constraints(self.cd_sys.clk, pll.clkin) # Ignore sys_clk to pll.clkin path created by SoC's rst.

        self.comb += self.cd_clkin.clk.eq(pll.clkin)

        # SDRAM clock
        sdram_clk = ClockSignal("sys_ps")
        self.specials += DDROutput(1, 0, platform.request("sdram_clock"), sdram_clk)

        # MC68040 clocks
        bclk = ClockSignal("bclk")
        self.specials += DDROutput(1, 0, platform.request("cpu_bclk"), bclk)

        pclk = ClockSignal("pclk")
        self.specials += DDROutput(1, 0, platform.request("cpu_pclk"), pclk)

# BaseSoC ------------------------------------------------------------------------------------------

class BaseSoC(SoCCore):
    def __init__(self, sys_clk_freq=int(80e6), **kwargs):
        platform = atx040.Platform()

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, sys_clk_freq,
            ident          = "LiteX SoC on ATX040",
            ident_version  = True,
            **kwargs)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq)

        self.cpu.add_pads(platform.request("mc68040"))

        self.comb += platform.request("rst_pu").eq(1)

        # SDR SDRAM --------------------------------------------------------------------------------
        if not self.integrated_main_ram_size:
            self.submodules.sdrphy = GENSDRPHY(platform.request("sdram"), sys_clk_freq)
            self.add_sdram("sdram",
                phy                     = self.sdrphy,
                module                  = MT48LC16M16(sys_clk_freq, "1:1"),
                origin                  = self.mem_map["main_ram"],
                size                    = kwargs.get("max_sdram_size", 0x40000000),
                l2_cache_size           = kwargs.get("l2_size", 2048),
                l2_cache_min_data_width = kwargs.get("min_l2_data_width", 128),
                l2_cache_reverse        = True
            )

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on MiniSpartan6")
    parser.add_argument("--build",        action="store_true", help="Build bitstream")
    parser.add_argument("--load",         action="store_true", help="Load bitstream")
    parser.add_argument("--sys-clk-freq", default=80e6,        help="System clock frequency (default: 80MHz)")
    builder_args(parser)
    soc_sdram_args(parser)
    args = parser.parse_args()

    soc = BaseSoC(
        sys_clk_freq = int(float(args.sys_clk_freq)),
        **soc_sdram_argdict(args)
    )
    builder = Builder(soc, **builder_argdict(args))
    builder.build(run=args.build)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(os.path.join(builder.gateware_dir, soc.build_name + ".bit"))

if __name__ == "__main__":
    main()
