OS9TOOL=~/coco/coco-dev/coco-dev imgtool
MAME_DIR=~/Applications/mame
MAME=$(MAME_DIR)/mame

TARGET=os9boot.dsk

TMPTARGET=os9boot.tmp
PLAYGROUND=playground
OS9BOOTSOURCE=$(PLAYGROUND)/NOS9_6809_L2_v030300_coco3_80d.dsk

RESOURCE_DIR=coco/resources/
RESOURCES=$(wildcard $(RESOURCE_DIR)/*)

EXAMPLE_DIR=examples
EXAMPLE_INPUT_DIR=$(EXAMPLE_DIR)/decb
EXAMPLES_INPUTS=$(wildcard $(EXAMPLE_INPUT_DIR)/*)

EXAMPLE_OUTPUT_DIR=$(EXAMPLE_DIR)/b09
EXAMPLES_OUTPUTS=$(wildcard $(EXAMPLE_OUTPUT_DIR)/*)


$(TARGET) : $(TMPTARGET) $(EXAMPLES_OUTPUT_DIR)/.updated $(RESOURCES)
	cp $(OS9BOOTSOURCE) $(TMPTARGET)
	bash -c 'for each in $(RESOURCE_DIR)/*; do $(OS9TOOL) put coco_jvc_os9 $(TMPTARGET) $${each} `basename $${each}`; done'
	bash -c 'for each in $(EXAMPLE_OUTPUT_DIR)/*; do $(OS9TOOL) put coco_jvc_os9 $(TMPTARGET) $${each} `basename $${each}`; done'
	mv $(TMPTARGET) $(TARGET)

$(TMPTARGET) :
	cp $(OS9BOOTSOURCE) $(TMPTARGET)

$(EXAMPLES_OUTPUT_DIR)/.updated : $(EXAMPLES_INPUTS)
	bash -c 'for each in $(EXAMPLE_INPUT_DIR)/*; do decb-to-b09 $${each} ${EXAMPLE_OUTPUT_DIR}/`basename $${each}`; done'

clean :
	rm -rf $(TARGET) $(TMPTARGET) build dist coco_tools.egg-info $(MODULE_DIR)/*~

run : $(TARGET)
	$(MAME) coco3 -rompath $(MAME_DIR)/roms -speed 4 -window -ext:fdc:wd17xx:0 525qd -flop1 $(TARGET)
