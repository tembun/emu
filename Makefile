SRCS:sh= find . -depth 1 -type f -not -name ".*" -not -name "Makefile" |sed 's/^\.\///'
PREFIX= /usr/local
BINDIR= bin
BIN_MODE= 0755
INSTALL= install
INSTALL_MODE_OPT= -m

all: ${SRCS:C/\..*//}
.for src in ${SRCS}
dest=${src:C/\..*//}
${PREFIX}/${BINDIR}/${dest}: ${src}
	@mkdir -p ${.TARGET:H}
	${INSTALL} ${INSTALL_MODE_OPT} ${BIN_MODE} ${.ALLSRC} ${.TARGET}

.PHONY: ${dest}
${dest}: ${PREFIX}/${BINDIR}/${dest}
.endfor
