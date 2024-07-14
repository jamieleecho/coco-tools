IMGTOOL=./coco-dev imgtool
MAME_DIR=~/Applications/mame
MAME=$(MAME_DIR)/mame

TARGET=os9boot.dsk
TARGET_DECB=basic.dsk

TMPTARGET=$(TARGET:.dsk=.tmp)
TMPTARGET_DECB=$(TARGET_DECB:.dsk=.tmp)
PLAYGROUND=playground
OS9BOOTSOURCE=$(PLAYGROUND)/NOS9_6809_L2_v030300_coco3_80d.dsk

RESOURCE_DIR=coco/resources
RESOURCES=$(wildcard $(RESOURCE_DIR)/*.b09)

EXAMPLE_DIR=examples
EXAMPLE_INPUT_DIR=$(EXAMPLE_DIR)/decb
EXAMPLES_INPUTS=$(wildcard $(EXAMPLE_INPUT_DIR)/*.bas)

EXAMPLE_OUTPUT_DIR=$(EXAMPLE_DIR)/b09
EXAMPLES_OUTPUTS=${subst $(EXAMPLE_INPUT_DIR), $(EXAMPLE_OUTPUT_DIR), $(EXAMPLES_INPUTS:.bas=.b09)}

all: build $(TARGET) $(TARGET_DECB)


lint:
	ruff check
	ruff linter

format:
	ruff format

build: lint
	python3 setup.py install

test:
	coverage run -m pytest && coverage report --show-missing

$(TARGET) : $(TMPTARGET) $(EXAMPLES_OUTPUTS) $(RESOURCES) build
	cp $(OS9BOOTSOURCE) $(TMPTARGET)
	bash -c 'for each in $(RESOURCE_DIR)/*.b09; do $(IMGTOOL) put coco_jvc_os9 $(TMPTARGET) $${each} `basename $${each}`; done'
	bash -c 'for each in $(EXAMPLE_OUTPUT_DIR)/*.b09; do $(IMGTOOL) put coco_jvc_os9 $(TMPTARGET) $${each} `basename $${each}`; done'
	mv $(TMPTARGET) $(@)

$(TARGET_DECB) : $(EXAMPLES_INPUTS)
	$(IMGTOOL) create coco_jvc_rsdos $(TMPTARGET_DECB)
	bash -c 'for each in $(EXAMPLES_INPUTS); do $(IMGTOOL) put coco_jvc_rsdos $(TMPTARGET_DECB) $${each} `echo $$(basename $${each}) | tr '[:lower:]' '[:upper:]'`  --ftype=basic --ascii=ascii; done'
	mv $(TMPTARGET_DECB) $(@)

$(TMPTARGET) :
	cp $(OS9BOOTSOURCE) $(TMPTARGET)

$(EXAMPLE_OUTPUT_DIR):
	mkdir -p $(EXAMPLE_OUTPUT_DIR)

$(EXAMPLE_OUTPUT_DIR)/%.b09: $(EXAMPLE_INPUT_DIR)/%.bas $(EXAMPLE_OUTPUT_DIR)
	decb-to-b09 -w $< $@

clean :
	rm -rf $(TARGET) $(TMPTARGET) $(TARGET_DECB) $(TMPTARGET_DECB) $(EXAMPLES_OUTPUTS) build dist coco_tools.egg-info $(MODULE_DIR)/*~

run :
	$(MAME) coco3 -rompath $(MAME_DIR)/roms -window -ext:fdc:wd17xx:0 525qd -flop1 $(TARGET)

runf :
	$(MAME) coco3 -rompath $(MAME_DIR)/roms -speed 4 -window -ext:fdc:wd17xx:0 525qd -flop1 $(TARGET)

decb :
	$(MAME) coco3 -rompath $(MAME_DIR)/roms -window -flop1 $(TARGET_DECB)

decbf :
	$(MAME) coco3 -rompath $(MAME_DIR)/roms  -speed 4 -window -flop1 $(TARGET_DECB)
