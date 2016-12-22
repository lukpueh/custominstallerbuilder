#!/bin/bash


# Seattle Software supply chain

# Start over from scratch
echo ""
echo "###########################"
echo "## Remove existing installer-packaging and base installers in $PWD"
rm -rf installer-packaging
rm -rf /Users/lukp/cib/custominstallerbuilder/html/static/installers/old_base_installers/*
rm -rf /Users/lukp/cib/custominstallerbuilder/html/static/installers/base/*;
rm -f *.link
rm -f linux_root.layout

echo ""
echo "###########################"
echo "## Create layout in $PWD"
python seattle_in_toto_layout.py linux

git clone https://github.com/SeattleTestbed/installer-packaging
cd installer-packaging/scripts

echo ""
echo "###########################"
echo "## Run step clone-dependencies in $PWD"
in-toto-run --step-name clone-dependencies --key ../../lukas \
  --products installer-packaging/DEPENDENCIES \
  --record-byproducts \
  -- python initialize.py

echo ""
echo "###########################"
echo "## Run step build-runnable in $PWD"
in-toto-run --step-name build-runnable --key ../../lukas \
  --materials installer-packaging/DEPENDENCIES \
  --products installer-packaging/RUNNABLE \
  --record-byproducts \
  -- python build.py

cd ../RUNNABLE

echo ""
echo "###########################"
echo "## Start step pre-build-file-edit in $PWD"
in-toto-record --step-name pre-build-file-edit --key ../../lukas \
  start --materials installer-packaging/RUNNABLE

echo ""
echo "###########################"
echo "## Manually editing files in $PWD"
cp ../../nmmain.py.edited seattle_repy/nmmain.py
cp ../../rebuild_base_installers.py.edited rebuild_base_installers.py
cp ../../softwareupdater.py.edited seattle_repy/softwareupdater.py


echo ""
echo "###########################"
echo "## End step pre-build-file-edit in $PWD"
in-toto-record --step-name pre-build-file-edit --key ../../lukas \
  stop --products installer-packaging/RUNNABLE

echo ""
echo "###########################"
echo "## Run step build-base-installers in $PWD"
in-toto-run --step-name build-base-installers --key ../../lukas \
  --materials installer-packaging/RUNNABLE \
  --products custominstallerbuilder/html/static/installers/base/ \
  --record-byproducts \
  -- python rebuild_base_installers.py 0.1-in-toto-in-seattle

cd ../..
echo ""
echo "###########################"
echo "## Run step dummy-untar-linux-base-installer $PWD"
in-toto-run --step-name dummy-untar-linux-base-installer --key lukas \
  --materials custominstallerbuilder/html/static/installers/base/seattle_linux.tgz \
  --products seattle \
  --record-byproducts \
  -- tar xf custominstallerbuilder/html/static/installers/base/seattle_linux.tgz

echo ""
echo "###########################"
echo "## Tar up link in-toto bundle and copy it to django static in $PWD"

mv installer-packaging/scripts/clone-dependencies.link .
mv installer-packaging/scripts/build-runnable.link .
mv installer-packaging/RUNNABLE/pre-build-file-edit.link .
mv installer-packaging/RUNNABLE/build-base-installers.link .
tar cf linux_seattle.in_toto_bundle.tar *.link albert.pub linux_root.layout
cp linux_seattle.in_toto_bundle.tar custominstallerbuilder/html/static/in-toto/
cp linux_seattle.in_toto_bundle.tar tmp/


# On client
# download linux installer
# download linux_seattle.in_toto_bundle.tar
# tar xf linux_seattle.in_toto_bundle.tar
# run:
# in-toto-verify --layout linux_root.layout --layout-keys albert.pub

