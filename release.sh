#!/bin/bash -e

sublime -w logcabin/__init__.py:5
VERSION=$(python setup.py --version)

# make changelog
echo -e "$VERSION\n" > changelog
git log --format='- %s%n' $(git describe --abbrev=0).. >> changelog
sublime -w README.rst:67 changelog
rm changelog

git add README.rst logcabin/__init__.py
git commit -m $VERSION
git push
python setup.py release

echo "$VERSION released"
