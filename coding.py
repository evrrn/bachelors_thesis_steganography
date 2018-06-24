from audiowave import Wave
from converter import WavConverter
from coder import BinaryMessage, Key, System


print("Поместите файлы аудиозаписи(*.mp3, *.m4a, *.wav) и сообщения(*.txt)")
print("в папку с данным приложением.")

print("Введите название файла аудиозаписи с расширением:")
audio = input()
print("Введите название файла сообщения с расширением:")
text = input()

audioconverter = WavConverter()
if audioconverter.is_needed(audio):
    audio = audioconverter.into_wav(audio)
    print("Для дальнейшей работы аудиозапись была переведена в формат wav.")

signal = Wave(audio)
message = BinaryMessage(text)
key = Key()

stegosystem = System(signal, message, key)
stegosystem.create_stego()
stegosystem.signal.create_stegoaudio(stegosystem.key)

audioconverter.delete_temps()

print("В папку с данным приложением сохранен файл с ключом key.txt и аудиофайл")
print("со скрытым сообщением out.wav.")

input()
