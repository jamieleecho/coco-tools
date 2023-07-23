OS9TOOL=~/coco/coco-dev/coco-dev imgtool
MAME_DIR=~/Applications/mame
MAME=$(MAME_DIR)/mame

TARGET=os9boot.dsk

TMPTARGET=os9boot.tmp
PLAYGROUND=playground
OS9BOOTSOURCE=$(PLAYGROUND)/NOS9_6809_L2_v030300_coco3_80d.dsk

RESOURCE_DIR=coco/resources
RESOURCES=$(wildcard $(RESOURCE_DIR)/*.b09)

EXAMPLE_DIR=examples
EXAMPLE_INPUT_DIR=$(EXAMPLE_DIR)/decb
EXAMPLES_INPUTS=$(wildcard $(EXAMPLE_INPUT_DIR)/*.bas)

EXAMPLE_OUTPUT_DIR=$(EXAMPLE_DIR)/b09
EXAMPLES_OUTPUTS=${subst $(EXAMPLE_INPUT_DIR), $(EXAMPLE_OUTPUT_DIR), $(EXAMPLES_INPUTS:.bas=.b09)}

all: build $(TARGET)

build:
	pycodestyle coco tests setup.py
	python3 setup.py install

$(TARGET) : $(TMPTARGET) $(EXAMPLES_OUTPUTS) $(RESOURCES) build
	cp $(OS9BOOTSOURCE) $(TMPTARGET)
	bash -c 'for each in $(RESOURCE_DIR)/*.b09; do $(OS9TOOL) put coco_jvc_os9 $(TMPTARGET) $${each} `basename $${each}`; done'
	bash -c 'for each in $(EXAMPLE_OUTPUT_DIR)/*.b09; do $(OS9TOOL) put coco_jvc_os9 $(TMPTARGET) $${each} `basename $${each}`; done'
	mv $(TMPTARGET) $(TARGET)

$(TMPTARGET) :
	cp $(OS9BOOTSOURCE) $(TMPTARGET)

$(EXAMPLE_OUTPUT_DIR)/%.b09: $(EXAMPLE_INPUT_DIR)/%.bas
	decb-to-b09 $< $@

clean :
	rm -rf $(TARGET) $(TMPTARGET) $(EXAMPLES_OUTPUTS) build dist coco_tools.egg-info $(MODULE_DIR)/*~

run :
	$(MAME) coco3 -rompath $(MAME_DIR)/roms -speed 4 -window -ext:fdc:wd17xx:0 525qd -flop1 $(TARGET)
