#!/bin/bash

# nice and simple :-)
tox || exit $?

# stash artifacts
cp -r .tox/dist $ARTIFACTS
cp -r .tox/docs/tmp/html $ARTIFACTS
