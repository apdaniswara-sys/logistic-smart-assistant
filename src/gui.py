import asyncio
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLineEdit, QLabel
from PySide6.QtCore import Qt
from assistant import answer_query_contextual
from nlp_voice import listen_and_recognize, speak

class LogisticAssistantGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logistic Smart Assistant")
        self.setGeometry(300, 100, 600, 500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.label = QLabel("Ketik Part No atau tekan 'Voice Command'")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Masukkan Part No...")
        layout.addWidget(self.input_line)

        btn_layout = QHBoxLayout()
        self.btn_query = QPushButton("Cari")
        self.btn_voice = QPushButton("Voice Command")
        btn_layout.addWidget(self.btn_query)
        btn_layout.addWidget(self.btn_voice)
        layout.addLayout(btn_layout)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)

        self.setLayout(layout)

        self.btn_query.clicked.connect(self.handle_query)
        self.btn_voice.clicked.connect(self.handle_voice_command)

        self.setStyleSheet("""
        QWidget {background-color: #f0f0f5; font-family: Arial; font-size: 14px;}
        QPushButton {background-color: #0078d7; color: white; border-radius: 5px; padding: 8px;}
        QPushButton:hover {background-color: #005a9e;}
        QLineEdit {padding: 5px; border-radius: 5px; border: 1px solid gray;}
        QTextEdit {background-color: #ffffff; border-radius: 5px;}
        """)

    def handle_query(self):
        user_text = self.input_line.text()
        if user_text:
            response = answer_query_contextual(user_text)
            self.text_area.append(f"> {user_text}\n{response}\n")
            asyncio.run(speak(response))

    def handle_voice_command(self):
        self.text_area.append("> Mendengarkan voice command...")
        user_text = listen_and_recognize()
        self.text_area.append(f"Anda: {user_text}")
        if user_text.lower() == "keluar":
            asyncio.run(speak("Terima kasih, sampai jumpa."))
            self.close()
            return
        response = answer_query_contextual(user_text)
        self.text_area.append(f"{response}\n")
        asyncio.run(speak(response))
