Automate Linux Seattle in-toto supply chain
---------

Setup CIB as described in:
https://github.com/SeattleTestbed/docs/blob/master/Operating/CustomInstallerBuilder/Installation.md
- Clone in-toto-in-seattle branch from https://github.com/lukpueh/custominstallerbuilder.git	
- In "Building base installers" only generate the cib keys and skip the rest of the section.

Install in-toto's seattle branch
- git clone -b seattle --recursive https://github.com/in-toto/in-toto.git

Copy scripts and files from this directory to its grand parent directory and run
./seattle_in_toto_supply_chain.sh

DISCLAIMER
Scripts might contain traces of "rm -rf"
ONLY FOR INTERNAL USE BY lukas.puehringer@nyu.edu"!!!
