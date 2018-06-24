import numpy
import math
from hamming_decoder import HammingDecoder


class BinaryMessage:
    def __init__(self):
        self.bits = []
        self.bitslen = 0
        self.output_txt = "message.txt"

    def set_bitslen(self):
        self.bitslen = len(self.bits)

    def save_text(self):
        output = open(self.output_txt, 'w')
        output.truncate()

        counter = 0
        bin_ord = ''

        flag = False
        left, right = "", ""
        code = HammingDecoder()

        self.set_bitslen()

        for i in range(self.bitslen):
            bin_ord += str(self.bits[i])
            counter += 1
            if counter == 7:
                if flag:
                    right = code.decode(bin_ord)
                    symb_ord = int(left + right, 2)

                    if symb_ord == 152 or 0 <= symb_ord <= 2:
                        letter = ' '
                    else:
                        byte_ord = int(symb_ord).to_bytes(1, byteorder='little')
                        letter = byte_ord.decode("cp1251")

                    output.write(letter)

                    flag = False
                    left, right = "", ""
                else:
                    left = code.decode(bin_ord)
                    flag = True
                bin_ord = ''
                counter = 0

        output.close()


class Key:
    def __init__(self, input_txt):
        input = open(input_txt, 'r').read().split(' ')
        self.delta = [int(input[0]), int(input[1])]
        self.begin, self.end = int(input[2]), int(input[3])


class System:
    def __init__(self, signal, message, key):
        self.signal = signal
        self.message = message
        self.key = key

        self.hidden_bits_per_second = 16
        self.samples_per_section = self.signal.frame_rate // self.hidden_bits_per_second
        self.diff = self.signal.frame_rate % self.hidden_bits_per_second

    def get_mod(self, x):
        return math.sqrt(x.real ** 2 + x.imag ** 2)

    def decode_section(self, section):
        extended_section = []
        extension = 4

        for s in section:
            for d in range(extension):
                extended_section.append(s - d)

        dft = numpy.fft.fft(extended_section)

        sqr_lg = []
        for elem in dft:
            sqr_lg.append((numpy.log(elem)) ** 2)

        ift = numpy.fft.ifft(sqr_lg)

        i0, i1 = extension*self.key.delta[0], extension*self.key.delta[1]
        imax0, imax1 = i0, i1

        for d in range(-2, 2):
            if self.get_mod(ift[i0 + d]) > self.get_mod(ift[imax0]):
                imax0 = i0 + d
            if self.get_mod(ift[i1 + d]) > self.get_mod(ift[imax1]):
                imax1 = i1 + d

        if self.get_mod(ift[imax0]) > self.get_mod(ift[imax1]):
            return "0"
        else:
            return "1"

    def extract_stegomessage(self):
        counter = self.key.begin
        section_counter = 0

        while counter < self.key.end:
            section = self.signal.channels[0][counter:counter + self.samples_per_section]
            self.message.bits.append(self.decode_section(section))

            counter += self.samples_per_section
            section_counter += 1

            if section_counter == self.hidden_bits_per_second:
                counter += self.diff
                section_counter = 0

        self.message.save_text()

