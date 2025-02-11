#!/usr/bin/env python3
"""
simple .nom parser and converter
"""

import argparse
import sys

ap = argparse.ArgumentParser(
  description='render .nom gloss draft into HTML'
)
ap.add_argument(
  'input',
  type=argparse.FileType('r'),
  default=sys.stdin,
  nargs='?'
)
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

ESC = '\\'
ESCS = ('', '-', '.', ESC)

def esc(ln_: int, s: str) -> str:
  if len(s) <= 2 and s[0] == ESC:
    char = s[1:]
    if char not in ESCS:
      die(ln_, f'Unknown escape {char!r}')
    # this syntax for inserting spc
    if not char:
      char = ' '
    s = char
  return s

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

  # handle sino-vocab marker
  if sino := line.startswith('-'):
    line = line[1:]  # rm it before splitting
  if line.count(' ') < 1:
    # optionally these are not annotated
    nom, quoc = esc(ln, line), ''
  else:
    # e.g.
    #   𡨸喃 quốc ngữ
    nom, quoc = line.split(' ', 1)
    if not quoc:
      die(ln, 'Missing quốc ngữ')
  if not nom:
    die(ln, 'Missing chữ nôm')

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
  else:
    # HACK: fix spc between words
    printf('<rb>&nbsp;</rb><rt></rt>', end='')

  # FIXME: dont add rt if quoc is empty
  printf(f'<rb>{nom}</rb><rt>{quoc}</rt>', end='')

# epilogue
if curr_sino is not None:
  printf('</ruby>')  # end last tag
printf('<!-- end -->')
printf('</body></html>')
