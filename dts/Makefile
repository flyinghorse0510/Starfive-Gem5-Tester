# Copyright (c) 2015-2016, 2019-2021 ARM Limited
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

CPP?=cpp
DTC?=dtc
NUM_DIES?=1

DTC_CPP_FLAGS=-nostdinc -undef

# $(1) is the prefix of DTB files
NUM_CPUS := 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16

CREATE_TARGET=$(foreach n, $(NUM_CPUS), $(if $(filter 0, $(shell expr $(n) % $(NUM_DIES))), $(1)_$(n)cpu_$(NUM_DIES)die.dtb))

TARGET_PREFIX=\
	VExpress_GEM5_V1 \
	VExpress_GEM5_V2 \
	VExpress_GEM5_V1_hdlcd \
	VExpress_GEM5_V2_hdlcd

TARGETS=\
	$(foreach prefix, $(TARGET_PREFIX), $(call CREATE_TARGET, $(prefix)))

VEXPRESS_GEM5_V1_DTSIS=\
	platforms/vexpress_gem5_v1_base.dtsi

VEXPRESS_GEM5_V1_HDLCD_DTSIS=\
	platforms/vexpress_gem5_v1_hdlcd.dtsi \
	platforms/vexpress_gem5_v1_base.dtsi

VEXPRESS_GEM5_V2_DTSIS=\
	platforms/vexpress_gem5_v2_base.dtsi

VEXPRESS_GEM5_V2_HDLCD_DTSIS=\
	platforms/vexpress_gem5_v2_hdlcd.dtsi \
	platforms/vexpress_gem5_v2_base.dtsi

GEN_DTS=mkdir -p .gen; \
	$(CPP) -x assembler-with-cpp \
		$(DTC_CPP_FLAGS) \
		-DCONF_PLATFORM=\"../platforms/$(1)\" \
		-DCONF_CPUS=$(2) \
		-DCONF_DIES=$(NUM_DIES) \
		-o $@ $<

all: $(TARGETS)

.gen/VExpress_GEM5_V1_%cpu_$(NUM_DIES)die.dts: armv8.dts \
	$(VEXPRESS_GEM5_V1_DTSIS)
	$(call GEN_DTS,vexpress_gem5_v1_base.dtsi,$*)

.gen/VExpress_GEM5_V1_hdlcd_%cpu_$(NUM_DIES)die.dts: armv8.dts \
	$(VEXPRESS_GEM5_V1_HDLCD_DTSIS)
	$(call GEN_DTS,vexpress_gem5_v1_hdlcd.dtsi,$*)

.gen/VExpress_GEM5_V2_%cpu_$(NUM_DIES)die.dts: armv8.dts \
	$(VEXPRESS_GEM5_V2_DTSIS)
	$(call GEN_DTS,vexpress_gem5_v2_base.dtsi,$*)

.gen/VExpress_GEM5_V2_hdlcd_%cpu_$(NUM_DIES)die.dts: armv8.dts \
	$(VEXPRESS_GEM5_V2_HDLCD_DTSIS)
	$(call GEN_DTS,vexpress_gem5_v2_hdlcd.dtsi,$*)

%.dtb: .gen/%.dts
	$(DTC) -I dts -O dtb -o $@ $<

clean:
	$(RM) -r .gen
	$(RM) *.dtb
