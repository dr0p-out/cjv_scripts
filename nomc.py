#!/usr/bin/env python3
"""
simple .nom parser and converter
"""

import argparse
import sys

ap = argparse.ArgumentParser(
  description='render .nom gloss draft into HTML'
)
ap.add_argument('input', type=argparse.FileType('r'))
ap.add_argument(
  '--output', '-o',
  type=argparse.FileType('w'),
  default=sys.stdout
)
argv = ap.parse_args()

def printf(*args, **kwargs):
  print(*args, **kwargs, file=argv.output)

def die(ln_: int, msg):
  print(f'L{ln_ + 1}: {msg}', file=sys.stderr)
  sys.exit(1)

# prologue
printf('''\
<!DOCTYPE html>
<html><head><style>
ruby { font-family: 'Gothic Nguyen'; font-size: 2.5em }
.sino { color: darkcyan }
</style></head><body>
<!-- begin -->
''', end='')

BR = '</br>'
LINE_BRKS = {
  '': BR,  # newline
  '.': BR * 2  # gap between lines
}

# this allow us to reuse tag for
# same line when no color change
curr_sino: bool | None = None  # dunno color yet

for ln, line in enumerate(argv.input):
  line = line.removesuffix('\n')  # py non-sense
  if line in LINE_BRKS:
    printf('</ruby>', end='')  # dont work inside tag?
    curr_sino: bool | None = None  # need new tag
    printf(LINE_BRKS[line])
    continue

  # e.g.
  #   𡨸喃 quốc ngữ
  if line.count(' ') < 1:
    die(ln, 'Missing quốc ngữ')
  # handle sino-vocab marker
  if sino := line.startswith('-'):
    line = line[1:]  # rm it before splitting
  # sep on 1st spc
  nom, quoc = line.split(' ', 1)
  if not nom or not quoc:
    die(ln, 'Missing text before/after space')

  # create a new tag first?
  if sino != curr_sino:
    # end current tag first (if any)
    if curr_sino is not None:
      printf('</ruby>')
    # highlight sino-vi words
    if sino:
      printf('<ruby class="sino">', end='')
    else:
      printf('<ruby>', end='')
    curr_sino = sino

  printf(f'<rb>{nom}</rb><rt>{quoc}</rt>', end='')

# epilogue
printf('</ruby>')  # end final tag
printf('<!-- end -->')
printf('</body></html>')
