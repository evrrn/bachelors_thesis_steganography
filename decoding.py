from audiowave import Wave
from decoder import BinaryMessage, Key, System


print("Поместите файл аудиозаписи(*.wav) и ключа(*.txt) в папку")
print("с данным приложением.")

print("Введите название файла аудиозаписи с расширением:")
audio = input()
print("Введите название файла ключа с расширением:")
text = input()

signal = Wave(audio)
message = BinaryMessage()
key = Key(text)

stegosystem = System(signal, message, key)
stegosystem.extract_stegomessage()

print("В папку с данным приложением сохранен файл с извлеченным")
print("сообщением message.txt.")

input()
