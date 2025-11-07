import sys
import asyncio
from PySide6.QtWidgets import QApplication
from src.gui import LogisticAssistantGUI

def main():
    """
    Entry point utama untuk Logistic Smart Assistant
    """
    app = QApplication(sys.argv)
    gui = LogisticAssistantGUI()
    gui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
