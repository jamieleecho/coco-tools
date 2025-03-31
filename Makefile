IMGTOOL=./coco-dev imgtool
DECB=./coco-dev decb
MAME_DIR=~/Applications/mame
MAME=$(MAME_DIR)/mame

TARGET=os9boot.dsk
TARGET_DECB=basic.dsk

STR_BUFFER_BYTES=200

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

.PHONY = \
	all \
    build-dist \
    default \
    check-all \
    check-lint \
    check-lock \
    clean \
    fix-all \
    fix-format \
    fix-lint \
    fix-lint-unsafe \
    help \
	install \
    install-pre-commit \
    lock \
    run-tests \
    sync

default: check-all run-tests

all: sync $(TARGET) $(TARGET_DECB)

build-dist: sync
	uv build --verbose --sdist

check-all: check-lint check-lock

check-lint:
	uv run ruff check

check-lock:
	uv lock --locked

clean:
	rm -rf .ruff_cache .venv build .cache *.egg-info dist $(TARGET) $(TMPTARGET) $(TARGET_DECB) $(TMPTARGET_DECB) $(EXAMPLES_OUTPUTS)

fix-all: fix-format fix-lint lock

fix-format:
	uv run ruff format

fix-lint:
	uv run ruff check --fix

fix-lint-unsafe:
	uv run ruff check --fix --unsafe-fixes

help:
	@echo ${.PHONY}

install: build-dist
	uv run pip install .

install-pre-commit:
	uv run pre-commit install

lock:
	uv lock

run-tests:
	uv run coverage run -m pytest
	coverage report --show-missing

sync:
	uv sync --no-install-workspace

$(TARGET) : $(EXAMPLES_OUTPUTS)
	cp $(OS9BOOTSOURCE) $(TMPTARGET)
	zsh -c 'for each in $(EXAMPLE_OUTPUT_DIR)/*.b09; do $(IMGTOOL) put coco_jvc_os9 $(TMPTARGET) $${each} `basename $${each}`; done'
	mv $(TMPTARGET) $(@)

$(TARGET_DECB) : $(EXAMPLES_INPUTS)
	$(DECB) dskini $(TMPTARGET_DECB)
	zsh -c 'for each in $(EXAMPLES_INPUTS); do $(DECB) copy -t $${each} $(TMPTARGET_DECB),`basename $${(U)each}`; done'
	mv $(TMPTARGET_DECB) $(@)

$(TMPTARGET) : $(OS9BOOTSOURCE)
	cp $(OS9BOOTSOURCE) $(TMPTARGET)

$(EXAMPLE_OUTPUT_DIR):
	mkdir -p $(EXAMPLE_OUTPUT_DIR)

$(EXAMPLE_OUTPUT_DIR)/%.b09: $(EXAMPLE_INPUT_DIR)/%.bas $(EXAMPLE_OUTPUT_DIR) $(RESOURCES)
	@if [ -f "`dirname $<`/`basename -a -s.bas $<`.yaml" ]; then \
		echo compiling $< with options; \
		decb-to-b09 -s$(STR_BUFFER_BYTES) -c "`dirname $<`/`basename -a -s.bas $<`.yaml" -w $< $@; \
	else \
		echo compiling $<; \
		decb-to-b09 -s$(STR_BUFFER_BYTES) -w $< $@; \
	fi

run :
	$(MAME) coco3 -rompath $(MAME_DIR)/roms -window -ext:fdc:wd17xx:0 525qd -flop1 $(TARGET)

runf :
	$(MAME) coco3 -rompath $(MAME_DIR)/roms -speed 4 -window -ext:fdc:wd17xx:0 525qd -flop1 $(TARGET)

decb :
	$(MAME) coco3 -rompath $(MAME_DIR)/roms -window -flop1 $(TARGET_DECB)

decbf :
	$(MAME) coco3 -rompath $(MAME_DIR)/roms  -speed 4 -window -flop1 $(TARGET_DECB)
