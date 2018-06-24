class HammingCoder:
    # the encoding matrix
    G = ['1101', '1011', '1000', '0111', '0100', '0010', '0001']

    def encode(self, x):
        y = ''.join([str(bin(int(i, 2) & int(x, 2)).count('1') % 2) for i in self.G])
        return y
