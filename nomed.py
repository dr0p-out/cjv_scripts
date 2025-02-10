#!/usr/bin/env python3
"""
minimalist real-time .nom writer
"""

import sys
import traceback

def err(*args, **kwargs):
  print(*args, **kwargs, file=sys.stderr)

try:
  from PySide6.QtCore import QEvent
  from PySide6.QtGui import QPalette
  from PySide6.QtWebEngineCore import QWebEngineSettings
  from PySide6.QtWebEngineWidgets import QWebEngineView
  from PySide6.QtWidgets import QApplication
except ImportError:
  traceback.print_exc()
  err('^^^ Tip: try installing pyside (if havent)')
  sys.exit(1)

class SucklessWebView(QWebEngineView):
  """
  HACK: HTML view w/ broken auto dark fixed
  FIXME: why is this needed
  """

  def __init__(self, *args, **kwargs):
    QWebEngineView.__init__(self, *args, **kwargs)
    self.setWindowTitle('HTML Previewer')
    # huh, wont launch if w/o content
    self.setHtml('')
    # ev wont fire at startup,
    # so run once immediately after
    self.__chk_do_dark()

  # FIXME: any closer way to be notified?
  def changeEvent(self, ev: QEvent):
    if ev.type() == QEvent.Type.PaletteChange:
      # app color theme changed
      self.__chk_do_dark()  # follow system
    QWebEngineView.changeEvent(self, ev)

  def __chk_do_dark(self):
    # FIXME: use proper way to determine
    palette = self.palette()
    bg = palette.color(QPalette.ColorRole.Window)
    fg = palette.color(QPalette.ColorRole.WindowText)
    # HACK: text usually brighter than UI
    is_dark = fg.value() > bg.value()

    # FIXME: get some better way for setting
    self.settings().setAttribute(
      QWebEngineSettings.WebAttribute.ForceDarkMode,
      is_dark
    )

qa = QApplication(sys.argv)

pv = SucklessWebView()
pv.show()

sys.exit(qa.exec())
