OS9TOOL=~/coco/coco-dev/coco-dev imgtool
MAME_DIR=~/Applications/mame
MAME=$(MAME_DIR)/mame

TARGET=os9boot.dsk

TMPTARGET=os9boot.tmp
PLAYGROUND=playground
OS9BOOTSOURCE=$(PLAYGROUND)/NOS9_6809_L2_v030300_coco3_80d.dsk
MODULE_DIR=$(PLAYGROUND)/modules
MODULES=$(wildcard $(MODULE_DIR)/*)


$(TARGET) : $(TMPTARGET) $(MODULES)
	cp $(OS9BOOTSOURCE) $(TMPTARGET)
	bash -c 'for each in $(MODULE_DIR)/*; do $(OS9TOOL) put coco_jvc_os9 $(TMPTARGET) $${each} `basename $${each}`; done'
	mv $(TMPTARGET) $(TARGET)

$(TMPTARGET) : 
	cp $(OS9BOOTSOURCE) $(TMPTARGET)

clean :
	rm -rf $(TARGET) $(TMPTARGET) build dist coco_tools.egg-info $(MODULE_DIR)/*~

run : $(TARGET)
	$(MAME) coco3 -rompath $(MAME_DIR)/roms -speed 4 -window -ext:fdc:wd17xx:0 525qd -flop1 $(TARGET)
