import math
import numpy
import random
from hamming_coder import HammingCoder


class BinaryMessage:
    def __init__(self, input_txt):
        self.bits = []
        self.input = open(input_txt, 'r')

        code = HammingCoder()

        for ch in self.input.read():
            symb_ord = ord(ch.encode('cp1251'))
            bin_ord = bin(symb_ord)[2:].zfill(8)

            left = bin_ord[:4]
            encoded_left = code.encode(left)
            for k in encoded_left:
                self.bits.append(int(k))

            right = bin_ord[4:]
            encoded_right = code.encode(right)
            for k in encoded_right:
                self.bits.append(int(k))

        self.average = numpy.mean(self.bits)
        self.bitslen = len(self.bits)


class Key:
    def __init__(self):
        self.delta = []
        self.begin, self.end = 0, 0
        self.output_txt = 'key.txt'

    def set_delta(self, delta):
        self.delta = delta

    def set_begin(self, begin):         # in sample's number
        self.begin = begin

    def set_end(self, end):       # in sample's number
        self.end = end

    def save(self):
        output = open(self.output_txt, 'w')
        output.truncate()
        output.write(" ".join((str(self.delta[0]), str(self.delta[1]), str(self.begin), str(self.end))))


class System:
    def __init__(self, signal, message, key):
        self.signal = signal
        self.message = message
        self.key = key

        self.echo_volume = 0.3
        self.hidden_bits_per_second = 16

        self.volume_max = 0.9
        self.volume_min = 0.7
        self.delta_max = 30
        self.delta_min = 40

        if self.message.average <= 0.5:
            self.volume0, self.volume1 = self.volume_max, self.volume_min
            self.key.set_delta([self.delta_max, self.delta_min])
        else:
            self.volume0, self.volume1 = self.volume_min, self.volume_max
            self.key.set_delta([self.delta_min, self.delta_max])

        # for separate channel
        self.samples_per_section = self.signal.frame_rate // self.hidden_bits_per_second
        self.diff = self.signal.frame_rate % self.hidden_bits_per_second

        self.samples_per_message = self.count_samples()     # for encoded message
        self.key.set_begin(self.get_begin())
        self.key.set_end(self.key.begin + self.samples_per_message)

        self.stegochannels = []

    def count_samples(self):
        div_part = self.message.bitslen // self.hidden_bits_per_second * self.signal.frame_rate
        mod_part = self.message.bitslen % self.hidden_bits_per_second * self.samples_per_section
        return div_part + mod_part

    def get_begin(self):        # in sample's number
        rest = self.signal.frames_num % self.signal.frame_rate
        acceptable_begin = self.signal.frames_num - self.samples_per_message - rest
        if acceptable_begin < 0:
            print("Текст слишком велик для аудиозаписи")
            return
        max_second = acceptable_begin // self.signal.frame_rate
        rand_second = random.randint(math.floor(max_second * 0.05), max_second)
        return rand_second * self.signal.frame_rate

    def smoothing_signal(self, i, position):
        x = self.message.bits[i]
        a = 0.0005
        b = 0.9995
        if x == 0:
            return 0.0
        k = position / self.samples_per_section
        if (a < k < b) or (a > k and i != 0 and int(self.message.bits[i - 1]) == x) \
                or (k > b and i + 1 != self.message.bitslen and int(self.message.bits[i + 1]) == x):
            return 1.0
        if a >= k:
            return k / a
        if k >= b:
            return (1.0 - k) / (1.0 - b)

    def get_echo(self, channel, k, n, counter):
        echo0 = self.volume0 * self.echo_volume * (channel[k - self.key.delta[0]] if k >= self.key.delta[0] else 0) * \
                (1 - self.smoothing_signal(counter, k - n))
        echo1 = self.volume1 * self.echo_volume * (channel[k - self.key.delta[1]] if k >= self.key.delta[1] else 0) * \
                self.smoothing_signal(counter, k - n)
        return echo0 + echo1

    def embed_stegomessage(self, channel):
        second_counter = self.key.begin // self.signal.frame_rate
        section_counter = 0
        volume = 1.0 - self.echo_volume * self.volume_max
        stegochannel = []

        for counter in range(self.message.bitslen):
            n = second_counter * self.signal.frame_rate + section_counter * self.samples_per_section
            for k in range(n, n + self.samples_per_section):
                stegochannel.append(math.floor(volume * channel[k] + self.get_echo(channel, k, n, counter)))
            section_counter += 1

            if section_counter == self.hidden_bits_per_second:
                for j in range(k, k + self.diff):
                    stegochannel.append(math.floor(volume * channel[j] + self.get_echo(channel, j, n, counter)))
                section_counter = 0
                second_counter += 1

        return stegochannel

    def create_stego(self):
        self.stegochannels.append(self.embed_stegomessage(self.signal.channels[0]))

        if self.signal.channels_num == 2:
            self.stegochannels.append((self.signal.channels[1])[self.key.begin:self.key.end])
            self.signal.stego = self.signal.unite_channels(self.stegochannels)
        else:
            self.signal.stego = self.stegochannels[0]

        self.key.save()
