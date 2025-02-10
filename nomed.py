#!/usr/bin/env python3
"""
minimalist real-time .nom writer
"""

import sys
import traceback

def err(*args, **kwargs):
  print(*args, **kwargs, file=sys.stderr)

try:
  from PySide6.QtCore import Qt, QEvent, Slot
  from PySide6.QtGui import QPalette, QShortcut
  from PySide6.QtWebEngineCore import QWebEngineSettings
  from PySide6.QtWebEngineWidgets import QWebEngineView
  from PySide6.QtWidgets import (
    QApplication,
    QPushButton, QTextEdit,
    QVBoxLayout, QWidget
  )
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

  def closeEvent(self, ev: QEvent):
    ed.close()  # closes each other
    QWebEngineView.closeEvent(self, ev)

class NomEdit(QTextEdit):
  def __init__(self, *args, **kwargs):
    QTextEdit.__init__(self, *args, **kwargs)
    self.setStyleSheet('font-family: "Gothic Nguyen"')
    self.setPlaceholderText('Type here…')
    self.setAcceptRichText(False)
    self.textChanged.connect(self.__handle_kb)

  @Slot()
  def __handle_kb(self):
    pass

class EditorWidget(QWidget):
  # no, we want to hold ref of these
  # pylint: disable=unused-private-member
  def __init__(self, *args, **kwargs):
    QWidget.__init__(self, *args, **kwargs)
    self.__layout = box = QVBoxLayout()
    self.setLayout(box)
    self.__btn = btn = QPushButton()
    btn.setText('保存／書き込み(S)')
    btn.clicked.connect(self.__do_save)
    box.addWidget(btn)
    self.__nom = nom = NomEdit()
    box.addWidget(nom)
    self.__keybind = key = QShortcut(self)
    key.setKey(Qt.Modifier.CTRL | Qt.Key.Key_S)
    key.activated.connect(self.__on_key_seq)
    self.setWindowTitle('Nôm Editor')

  def closeEvent(self, ev: QEvent):
    pv.close()  # closes each other
    QWidget.closeEvent(self, ev)

  @Slot()
  def __on_key_seq(self):
    self.__btn.animateClick()

  @Slot()
  def __do_save(self):
    pass

qa = QApplication(sys.argv)

pv = SucklessWebView()
pv.show()
ed = EditorWidget()
ed.show()

sys.exit(qa.exec())
