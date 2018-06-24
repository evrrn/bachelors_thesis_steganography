import numpy
import wave
import math


class Wave:
    types = {
        1: numpy.int8,
        2: numpy.int16,
        4: numpy.int32
    }

    def __init__(self, input_wav):
        self.wavein = wave.open(input_wav, 'r')
        self.channels_num = self.wavein.getnchannels()  # mono / stereo
        self.bytes_per_sample = self.wavein.getsampwidth()  # 1 / 2 / 4
        self.frame_rate = self.wavein.getframerate()  # 8000 / 44100 / 48000 / 96000
        self.frames_num = self.wavein.getnframes()
        self.content = numpy.fromstring(self.wavein.readframes(self.frames_num),
                                        dtype=self.types[self.bytes_per_sample])
        self.wavein.close()

        self.channels = []
        for n in range(self.channels_num):
            self.channels.append(self.content[n::self.channels_num])

        self.stego = []
        self.switching = 3 * self.frame_rate

        # for united channels
        self.decreasing_from = 0
        self.increasing_to = 0

    def set_decreasing_from(self, key):
        self.decreasing_from = max(0, key.begin - self.switching) * self.channels_num

    def set_increasing_to(self, key):
        self.increasing_to = min(self.frames_num, key.end + self.switching) * self.channels_num

    def set_amplitude(self, inst_amp):
        content = []
        for a in inst_amp:
            amp_in_bytes = int(a).to_bytes(self.bytes_per_sample, byteorder='little', signed=True)
            for part in amp_in_bytes:
                content.append(part)
        return bytearray(content)

    def unite_channels(self, channels):
        content = []
        for i in range(len(channels[0])):
            for j in range(2):
                content.append(channels[j][i])
        return content

    def dec_signal(self, i, begin):
        if self.channels_num == 2 and i % 2 == 1:
            return 1.0
        return 1.0 - 0.2 * i / (begin - self.decreasing_from)

    def inc_signal(self, i, end):
        if self.channels_num == 2 and i % 2 == 1:
            return 1.0
        return 0.8 + 0.2 * i / (self.increasing_to - end)

    def create_stegoaudio(self, key):
        output_wav = 'out.wav'
        wave_out = wave.open(output_wav, 'w')
        wave_out.setparams(self.wavein.getparams())

        self.set_decreasing_from(key)
        self.set_increasing_to(key)

        wave_out.writeframesraw(self.content[:self.decreasing_from])        # begin
        dec = [math.floor(self.dec_signal(i, key.begin * self.channels_num) * amp) for i, amp
               in enumerate(self.content[self.decreasing_from:key.begin * self.channels_num])]
        wave_out.writeframesraw(self.set_amplitude(dec))        # decreasing

        wave_out.writeframesraw(self.set_amplitude(self.stego))

        inc = [math.floor(self.inc_signal(i, key.end * self.channels_num) * amp) for i, amp
               in enumerate(self.content[key.end * self.channels_num:self.increasing_to])]
        wave_out.writeframesraw(self.set_amplitude(inc))        # increasing
        wave_out.writeframesraw(self.content[self.increasing_to:])      # end

        wave_out.close()
