import sys
from in_toto import util
from in_toto.models.layout import Step, Inspection, Layout

from datetime import datetime
from dateutil.relativedelta import relativedelta

util.generate_and_write_rsa_keypair("albert")
util.generate_and_write_rsa_keypair("lukas")

root_key = util.import_rsa_key_from_file("albert")
func_key = util.import_rsa_key_from_file("lukas")
func_pubkey = util.import_rsa_key_from_file("lukas.pub")
func_id = func_key["keyid"]

def create_common_steps():

  steps = [

    Step(
      name="clone-dependencies",
      expected_command=\
          "python initialize.py",
      product_matchrules=[

          "CREATE installer-packaging/*".split(),
      ],
      pubkeys=[func_id]
    ),
    Step(
      name="build-runnable",
      expected_command=\
          "python build.py",
      material_matchrules=[
          "MATCH PRODUCT installer-packaging/* FROM clone-dependencies".split(),
      ],
      product_matchrules=[
          "CREATE installer-packaging/*".split(),
      ],
      pubkeys=[func_id]
    ),
    Step(
      name="pre-build-file-edit",
      expected_command="edit files manually",
      material_matchrules=[
          "MATCH PRODUCT installer-packaging/RUNNABLE/* FROM build-runnable"
          .split(),
      ],
      product_matchrules=[
          "CREATE installer-packaging/*".split(),
      ],
      pubkeys=[func_id]
    ),

    Step(
      name="build-base-installers",
      expected_command=\
          "python rebuild_base_installers.py 0.1-in-toto-in-seattle",
      material_matchrules=[
          "MATCH PRODUCT installer-packaging/* FROM pre-build-file-edit"
          .split(),
      ],
      product_matchrules=[
          "CREATE custominstallerbuilder/html/static/installers/base/*"
          .split(),
      ],
      pubkeys=[func_id]
    )]

  # TODO
  # the build-installer step is part of the Django app module build_manager
  # it would need to be modified to call into in-toto library

  # step_build_installer = Step(
  #     name="build-installer",
  #     expected_command=\
  #         None
  #     material_matchrules=[
  #         "MATCH ../../custominstallerbuilder/html/static/installers/base/*"
  #         .split(),
  #     ],
  #     product_matchrules=[
  #         .split(),
  #     ],
  #     pubkeys=[func_id]
  #   )

  return steps

def create_layout(steps, inspects, name):
  layout = Layout(
      steps=steps,
      inspect=inspects,
      keys={
        func_id: func_pubkey
      },
      expires=((datetime.today() + relativedelta(months=1)).isoformat() + 'Z')
    )

  layout.sign(root_key)
  layout.dump(name)

def linux():
  common_steps = create_common_steps()
  # FIXME
  # build-base-installers is a complex compound step that
  # fetches files from different locations and places them directly into a tar
  #
  # Add this dummy step to allow an untar Inspection to match all files from the
  # untared base installer using a wildcard
  step_untar_base_installer = Step(
      name="dummy-untar-linux-base-installer",
      material_matchrules=[
        ["MATCH", "PRODUCT",
        "custominstallerbuilder/html/static/installers/base/seattle_linux.tgz",
        "FROM",
        "build-base-installers"]
      ],
      product_matchrules=[
        "CREATE *".split()
      ],
      expected_command=("tar xf "
        "custominstallerbuilder/html/static/installers/base/seattle_linux.tgz"),
      pubkeys=[func_id]

    )

  inspection_untar_linux = Inspection(
      name="untar-linux-installer",
      material_matchrules=[
        "CREATE *".split()
      ],
      product_matchrules=[
        "CREATE seattle/seattle_repy/vesselinfo".split(),
        "MATCH PRODUCT seattle/* FROM dummy-untar-linux-base-installer".split(),
        "CREATE *".split()
      ],
      run="tar xf seattle_linux.tgz"
    )
  steps = common_steps + [step_untar_base_installer]
  inspects = [inspection_untar_linux]
  create_layout(steps, inspects, "linux_root.layout")


def android():
  raise Exception("Not Implemented")

def mac():
  raise Exception("Not Implemented")

def win():
  raise Exception("Not Implemented")



def usage():
  print "Usage:", sys.argv[0], "(linux | mac | android | win)"

def main():

  if len(sys.argv) < 2:
    usage()
    sys.exit(1)

  if sys.argv[1] == "linux":
    linux()
  elif sys.argv[1] == "mac":
    mac()
  elif sys.argv[1] == "android":
    android()
  elif sys.argv[1] == "win":
    win()
  else:
    usage()
    sys.exit(1)

if __name__ == '__main__':
  main()