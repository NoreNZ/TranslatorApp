import os #file and directory operations
import sys
import speech_recognition as sr #speech recognition, used for speech transcription
import threading #multithreading
import requests #HTTP requests, used to translate text through MyMemory API
from elevenlabs import set_api_key, generate, save #Elevenlabs API for speech synthesis
import soundfile as sf #Audio processing
import simpleaudio as sa #Audio playback
from PyQt5 import QtCore, QtGui, QtWidgets #GUI

# Set the API key for the translation service
set_api_key("b84b0ec25287434619d3a7a8701542c6")


#Speech translation application
class SpeechTranslatorApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Speech Translator") #Window title
        self.setGeometry(100, 100, 800, 400) #Window dimensions

        self.stop_listening = False #Bool for status of user microphone input
        self.r = sr.Recognizer() #Create instance of speech recognizer
        self.mic = sr.Microphone() #Create instance of microphone

        self.setup_ui() #Call setup GUI

    #Setup application GUI
    def setup_ui(self):
        #Input language button label
        self.input_label = QtWidgets.QLabel("Input Language", self)
        self.input_label.setAlignment(QtCore.Qt.AlignCenter)
        self.input_label.move(20, 20)

        #Input language dropdown box, 8 selectable languages
        self.input_dropdown = QtWidgets.QComboBox(self)
        self.input_dropdown.addItems(["English", "German", "Polish", "Spanish", "Italian", "French", "Portuguese", "Hindi"])
        self.input_dropdown.setCurrentText("English")

        #Switch language button
        self.switch_button = QtWidgets.QPushButton(self)
        self.switch_button.setIcon(QtGui.QIcon("switch_icon.png"))
        self.switch_button.setIconSize(QtCore.QSize(24, 24))
        self.switch_button.clicked.connect(self.switch_languages)

        #Output language button label
        self.output_label = QtWidgets.QLabel("Output Language", self)
        self.output_label.setAlignment(QtCore.Qt.AlignCenter)
        self.output_label.move(270, 20)

        #Output language button, 8 selectable languages
        self.output_dropdown = QtWidgets.QComboBox(self)
        self.output_dropdown.addItems(["English", "German", "Polish", "Spanish", "Italian", "French", "Portuguese", "Hindi"])
        self.output_dropdown.setCurrentText("English")

        #Voice button label
        self.voice_label = QtWidgets.QLabel("Voice", self)
        self.voice_label.setAlignment(QtCore.Qt.AlignCenter)
        self.voice_label.move(500, 20)

        #Voice selection, 4 selectable voices
        self.voice_dropdown = QtWidgets.QComboBox(self)
        self.voice_dropdown.addItems(["Adam", "Antoni", "Bella", "Rachel"])
        self.voice_dropdown.setCurrentText("Adam")

        #Start button begins speech transcription
        self.toggle_button = QtWidgets.QPushButton("Start", self)
        self.toggle_button.clicked.connect(self.toggle_microphone)

        #Translate button translates input text and print in output langauge in output box
        self.translate_button = QtWidgets.QPushButton("Translate", self)
        self.translate_button.clicked.connect(self.translate_text)

        #Sets input text box to read only false, allows user to type in what they want to translate
        self.mic_transcription = QtWidgets.QPlainTextEdit(self)
        self.mic_transcription.setReadOnly(False)

        #Sets output text box to read only true, doesn't allow user to type in what they want to translate
        self.translated_text = QtWidgets.QPlainTextEdit(self)
        self.translated_text.setReadOnly(True)

        #Text to speech for input box
        self.speak_input_button = QtWidgets.QPushButton("Speak", self)
        self.speak_input_button.clicked.connect(self.speak_input_text)

        #Text to speech for output box
        self.speak_output_button = QtWidgets.QPushButton("Speak", self)
        self.speak_output_button.clicked.connect(self.speak_output_text)

        #Setup and update button positions function
        self.update_button_positions()

        # Set window icon
        icon = QtGui.QIcon("icon.jpg")
        self.setWindowIcon(icon)


    #Setup and update button positions
    def update_button_positions(self):
        toggle_button_width = self.toggle_button.width()
        translate_button_width = self.translate_button.width()
        dropdown_width = (self.width() - toggle_button_width - translate_button_width - 10) // 2.52

        self.input_dropdown.setGeometry(20, 60, dropdown_width, 30)

        switch_button_x = 20 + dropdown_width + 10
        switch_button_width = 30
        switch_button_height = 30
        switch_button_y = 60 + (self.input_dropdown.height() - switch_button_height) // 2
        self.switch_button.setGeometry(switch_button_x, switch_button_y, switch_button_width, switch_button_height)

        output_dropdown_x = switch_button_x + switch_button_width + 10
        self.output_dropdown.setGeometry(output_dropdown_x, 60, dropdown_width, 30)

        voice_dropdown_x = output_dropdown_x + dropdown_width + 10
        self.voice_dropdown.setGeometry(voice_dropdown_x, 60, dropdown_width, 30)

        # Move button labels with corresponding dropdowns
        input_label_x = 20
        input_label_y = self.input_dropdown.y() - 25
        self.input_label.move(input_label_x, input_label_y)

        switch_button_x = self.switch_button.x()
        switch_button_y = self.input_dropdown.y() + (self.input_dropdown.height() - switch_button_height) // 2
        self.switch_button.setGeometry(switch_button_x, switch_button_y, switch_button_width, switch_button_height)

        output_label_x = output_dropdown_x
        output_label_y = self.output_dropdown.y() - 25
        self.output_label.move(output_label_x, output_label_y)

        voice_label_x = voice_dropdown_x
        voice_label_y = self.voice_dropdown.y() - 25
        self.voice_label.move(voice_label_x, voice_label_y)

        self.toggle_button.move(self.width() // 2 - self.toggle_button.width() - 10, 90)
        self.translate_button.move(self.width() // 2 + 10, 90)
        self.mic_transcription.setGeometry(20, 140, self.width() // 2 - 30, 200)
        self.translated_text.setGeometry(self.width() // 2 + 10, 140, self.width() // 2 - 30, 200)
        self.speak_input_button.setGeometry(20, 350, self.width() // 2 - 30, 30)
        self.speak_output_button.setGeometry(self.width() // 2 + 10, 350, self.width() // 2 - 30, 30)

    #QtWidgets UI function called when window is resized
    def resizeEvent(self, event):
        self.update_button_positions()

    #Switch button logic for switching languages
    def switch_languages(self):
        input_text = self.input_dropdown.currentText()
        output_text = self.output_dropdown.currentText()
        self.input_dropdown.setCurrentText(output_text)
        self.output_dropdown.setCurrentText(input_text)

    #Function called when 'start' button is pressed, calls speech transcription function
    def toggle_microphone(self):
        if self.stop_listening:
            #Change microphone bool to False
            self.stop_listening = False
            #Update button text
            self.toggle_button.setText("Stop")
            #Transcribe user audio input
            threading.Thread(target=self.transcribe_audio).start()
            #Disable both speak buttons while transcribing
            self.speak_input_button.setEnabled(False)
            self.speak_output_button.setEnabled(False)
        else:
            #When user stops microphone input 
            self.stop_listening = True
            #Update button text
            self.toggle_button.setText("Start")
            #Re-enable speak buttons
            self.speak_input_button.setEnabled(True)

    #Speech transcription function
    def transcribe_audio(self):
        #While microphone is enabled
        while not self.stop_listening:
            try:
                with self.mic as source:
                    #Speech recognizer listens to microphone
                    audio = self.r.listen(source)
                #Transcribes user input
                transcription = self.r.recognize_google(audio)
                #Append new line to transcription
                self.mic_transcription.appendPlainText(transcription + "\n")
            except sr.UnknownValueError:
                #Error transcribing
                print("Audio could not be transcribed")

    #Text translation function using mymemory web api
    def translate_text(self):
        #Strip transcription text
        text = self.mic_transcription.toPlainText().strip()
        if text:
            #HTTP request to translation API mymemory
            url = f"https://api.mymemory.translated.net/get?q={text}&langpair={self.input_dropdown.currentText()}|{self.output_dropdown.currentText()}"
            response = requests.get(url)
            translated = response.json()["responseData"]["translatedText"]
            #Append newline to translated text
            self.translated_text.setPlainText(translated + "\n")
            #Enabled speak button
            self.speak_output_button.setEnabled(True)
            #Calls speak function for translated text
            threading.Thread(target=self.speak, args=(translated,)).start()
        else:
            #Disable speak button
            self.speak_output_button.setEnabled(False)

    #Text to speech for input text box
    def speak_input_text(self):
        #Retrieve text to synthesize
        text = self.mic_transcription.toPlainText().strip()
        if text:
            #Synthesize speech
            threading.Thread(target=self.speak, args=(text,)).start()

    #Text to  speech for output text box
    def speak_output_text(self):
        #Retrieve text to synthesize
        text = self.translated_text.toPlainText().strip()
        if text:
            #Synthesize speech
            threading.Thread(target=self.speak, args=(text,)).start()

    #Text to speech function using Elevenlabs multilingual API
    def speak(self, text):
        audio = generate(
            text=text,
            voice=self.voice_dropdown.currentText(),
            model="eleven_multilingual_v1"
        )
        #Define directory for audio file to save and load from
        current_dir = os.path.dirname(os.path.abspath(__file__))
        audio_file = os.path.join(current_dir, "temp_audio.wav")
        #Save audio file to directory
        save(audio, audio_file)
        #Conver to Wav, playback errors despite already being WAV
        self.convert_to_wav(audio_file)
        #Play audio file
        self.play_audio(audio_file)

    #Convert audio file to wav format
    def convert_to_wav(self, file_path):
        output_file = os.path.splitext(file_path)[0] + ".wav"
        audio, sample_rate = sf.read(file_path)
        sf.write(output_file, audio, sample_rate)

    #Play audio file
    def play_audio(self, file_path):
        CHUNK = 1024
        wf = sa.WaveObject.from_wave_file(file_path)
        play_obj = wf.play()
        play_obj.wait_done()

    def center_align_text(self, text_edit):
        option = QtGui.QTextOption(QtCore.Qt.AlignmentFlag.AlignCenter)
        text_edit.document().setDefaultTextOption(option)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = SpeechTranslatorApp()
    window.show()
    sys.exit(app.exec_())
