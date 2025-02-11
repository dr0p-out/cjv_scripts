#!/usr/bin/env python3
"""
minimalist real-time .nom writer
"""

import os.path
import sys
import traceback

def err(*args, **kwargs):
  print(*args, **kwargs, file=sys.stderr)

try:
  from PySide6.QtCore import (
    Qt, QCommandLineOption, QCommandLineParser, QEvent,
    QProcess,
    QTimer, Slot
  )
  from PySide6.QtGui import QPalette, QShortcut
  from PySide6.QtWebEngineCore import QWebEngineSettings
  from PySide6.QtWebEngineWidgets import QWebEngineView
  from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
    QPlainTextEdit, QPushButton,
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

BINDIR = os.path.dirname(__file__)
NOMC_PATH = os.path.join(BINDIR, 'nomc.py')

class NomEdit(QPlainTextEdit):
  # let us hold obj ownership
  # pylint: disable=unused-private-member
  def __init__(self, *args, **kwargs):
    QPlainTextEdit.__init__(self, *args, **kwargs)
    self.setStyleSheet('font-family: "Gothic Nguyen"')
    self.setPlaceholderText('Type here…')
    self.textChanged.connect(self.__handle_kb)
    self.__timer: QTimer | None = None
    self.__proc: QProcess | None = None

  @Slot()
  def __handle_kb(self):
    # re-render only after a small idle for perf
    # SAFETY: we're single-thr
    if (t := self.__timer) and t.isActive():
      t.stop()
    self.__timer = t = QTimer()
    t.setInterval(1000)
    t.setSingleShot(True)
    t.timeout.connect(self.__do_render)
    t.start()

  @Slot()
  def __do_render(self):
    self.__proc = p = QProcess()
    p.setProgram(NOMC_PATH)
    p.setArguments(('-', '-o', '-'))
    p.errorOccurred.connect(self.__on_err)
    p.finished.connect(self.__on_finish)
    p.started.connect(self.__on_started)
    p.start()

  @Slot()
  def __on_err(self, err: QProcess.ProcessError):
    # usually, fork()/exec() failure
    self.__show_err(self.__proc.errorString())

  def __show_err(self, s: str):
    b = s.encode()
    pv.setContent(b, 'text/plain;charset=UTF-8')

  @Slot()
  def __on_finish(self):
    # usually, exit() called
    if (p := self.__proc).exitCode() == 0:
      # nomc succeeded
      html = p.readAllStandardOutput()
      try:
        # TODO: workaround 2MB limit
        pv.setHtml(html.data().decode())
      except UnicodeDecodeError:
        self.__show_err('Output contains invalid char')
    else:
      # nomc failed
      err = p.readAllStandardError()
      try:
        self.__show_err(err.data().decode())
      except UnicodeDecodeError:
        self.__show_err('Error contains invalid char')

  @Slot()
  def __on_started(self):
    data = self.toPlainText().encode()
    (p := self.__proc).write(data)
    p.closeWriteChannel()  # eof

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
    btn.setDisabled(True)
    box.addWidget(btn)
    self.__nom = nom = NomEdit()
    box.addWidget(nom)
    self.__keybind = key = QShortcut(self)
    key.setKey(Qt.Modifier.CTRL | Qt.Key.Key_S)
    key.activated.connect(self.__on_key_seq)
    self.setWindowTitle('Nôm Editor')

    view_only = ap.isSet(opt_v)
    if view_only:
      nom.setReadOnly(True)

    if argv:
      # try to populate content
      try:
        with open(argv[0], 'r') as f:
          # this alr triggers render
          nom.setPlainText(f.read())
      except OSError as e:
        QMessageBox.warning(
          self,
          'Warning',
          f'Unable to read input file {argv[0]!r}:'
          f'\n\n{e.strerror}'
        )
      except UnicodeDecodeError:
        QMessageBox.warning(
          self,
          'Warning',
          f'Rejecting input file {argv[0]!r} '
          'containing invalid char.'
        )
      else:
        if not view_only:
          btn.setEnabled(True)

  def closeEvent(self, ev: QEvent):
    pv.close()  # closes each other
    QWidget.closeEvent(self, ev)

  @Slot()
  def __on_key_seq(self):
    self.__btn.animateClick()

  @Slot()
  def __do_save(self):
    try:
      with open(argv[0], 'w') as f:
        f.write(self.__nom.toPlainText())
    except OSError as e:
      QMessageBox.warning(
        self,
        'Warning',
        f'Failed writing output file {argv[0]!r}:'
        f'\n\n{e.strerror}'
      )

class CloseKeyBind(QShortcut):
  def __init__(self, *args, **kwargs):
    QShortcut.__init__(self, *args, **kwargs)
    self.setKey(Qt.Modifier.CTRL | Qt.Key.Key_W)
    self.activated.connect(self.__do_close)

  @Slot()
  def __do_close(self):
    qa.quit()

qa = QApplication(sys.argv)
ap = QCommandLineParser()
ap.setApplicationDescription(
  'small Qt-based GUI frontend for editing .nom'
)
ap.addHelpOption()
ap.addPositionalArgument('file', '')
opt_v = QCommandLineOption(
  ('v', 'view'),
  'Open file in viewer (read-only) mode.'
)
ap.addOption(opt_v)
ap.process(qa)
argv = ap.positionalArguments()
if len(argv) > 1:
  err(
    f'{sys.argv[0]}: Too many positional arguments'
  )
  sys.exit(1)

roots = []
roots.append(pv := SucklessWebView())
pv.show()
roots.append(ed := EditorWidget())
ed.show()
quit_keys = [ CloseKeyBind(root) for root in roots ]

sys.exit(qa.exec())
