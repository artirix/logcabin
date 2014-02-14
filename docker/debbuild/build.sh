#!/bin/bash -e

: ${PACKAGE:?must be set}

BASENAME=$(basename $PACKAGE)
DIRNAME=${BASENAME%.tar.gz}

mkdir /tmp/build
cd /tmp/build
wget $PACKAGE

py2dsc -x /stdeb.cfg $BASENAME
cd deb_dist/$DIRNAME
dpkg-buildpackage
