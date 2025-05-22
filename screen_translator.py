import sys
import pytesseract
import traceback
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QLabel, QMessageBox
from PyQt5.QtCore import Qt, QTimer, QEvent
from PIL import ImageGrab
from deep_translator import GoogleTranslator

class OverlayLabel(QWidget):
    def __init__(self, text, bbox):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        x, y, w, h = bbox
        self.setGeometry(x, y, w, h)
        label = QLabel(text, self)
        label.setStyleSheet("background: rgba(255,255,200,200); color: black; font-size: 16px;")
        label.setWordWrap(True)
        label.setGeometry(0, 0, w, h)
        self.show()

class FloatingButton(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setGeometry(50, 50, 60, 60)
        self.button = QPushButton('🎯', self)
        self.button.resize(60, 60)
        self.button.clicked.connect(self.parent.translate_screen)
        self.show()
        self._drag_active = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_active = True
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_active and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_active = False

class TranslatorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.translating = False
        self.overlays = []
        self.initUI()
        self.floating_button = FloatingButton(self)
        self.floating_button.hide()

    def initUI(self):
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setGeometry(200, 200, 300, 100)
        self.button = QPushButton('Traduire l\'écran', self)
        self.button.clicked.connect(self.show_floating_button)
        self.button.resize(200, 60)
        self.button.move(50, 20)
        self.show()

    def show_floating_button(self):
        self.floating_button.show()

    def translate_screen(self):
        try:
            # Fermer les anciens overlays
            for overlay in self.overlays:
                overlay.close()
            self.overlays = []
            img = ImageGrab.grab()
            data = pytesseract.image_to_data(img, lang='eng', output_type=pytesseract.Output.DICT)
            n_boxes = len(data['level'])

            for i in range(n_boxes):
                # 5 = niveau "line" dans pytesseract (souvent une phrase complète)
                if data['level'][i] == 5:
                    phrase = data['text'][i].strip()
                    if phrase:
                        x = data['left'][i]
                        y = data['top'][i]
                        w = data['width'][i]
                        h = data['height'][i]
                        translated = GoogleTranslator(source='en', target='fr').translate(phrase)
                        overlay = OverlayLabel(translated, (x, y, w, h))
                        self.overlays.append(overlay)
        except Exception as e:
            error_msg = traceback.format_exc()
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue :\n{error_msg}")

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                QTimer.singleShot(0, self.hide)
                self.floating_button.show()
        super().changeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TranslatorWidget()
    sys.exit(app.exec_())