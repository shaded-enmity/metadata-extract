#!/usr/bin/bash

if [[ "$1" = '-h' || "$1" = '--help' ]]; then 
  echo $(basename $0) "[-h | --help] FILE"
  echo ; echo -ne 'FILE\tArchive (TAR) to analyze\n'
  echo ; echo 'FILE is extracted and files are scanned using several tools'
  exit 0
fi

INFILE=$1
DIR=${INFILE}_metadata

rm -rf ${DIR}
mkdir -p ${DIR}
echo '=> extracting' $(sha256sum ${INFILE})

# unpack into `_metadata`
tar xf ${INFILE} -C ${DIR}

echo '=> Directory structure'
tree ${DIR}

echo '=> '
for FL in $(find ${DIR}/); do
  if [[ ! -d "$FL" ]]; then
    echo "==> Processing ${FL} {" $(sha256sum ${FL} | cut -d' ' -f1) "}"
    # identify basic file type
    file ${FL} | cut -d' ' -f2-
    # scan language types (sometimes crashes :)
    linguist ${FL} 2>/dev/null
    # advanced content analysis
    binwalk -B ${FL} | tail -n +4 | sed 's,^\w*\ *\w*\ *,,'
  fi
done
echo '=> done!'
echo '=> package license:'
# search license in setup.py
echo '==> ' $(cat $(find ${DIR}/ -name 'setup.py') | grep "license=[\"']" | sed "s,license=['\"]\(.*\)['\"].*,\1,g")
# inspect setup.py's AST using redhawk
echo '=> inspecting "setup.py" '$(2>&1 python  --version) ' AST:'
#redhawk show -i -e $(find ${DIR}/ -name 'setup.py')
redhawk show $(find ${DIR}/ -name 'setup.py')
# linguist needs a git repo
(cd ${DIR}/ && git init && git add * && git commit -m "repo") 2>&1 1>/dev/null 
echo '=> language composition:'
linguist ${DIR}
