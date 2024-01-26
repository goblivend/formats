import zlib

def ones_complement(n, nb_bits):
    return ((1 << nb_bits) - 1) ^ n

class PngEncoder:
    def __init__(self, arr, debug=False) :
        self.data = arr
        self.width = len(arr[0])
        self.height = len(arr)
        self.palette = None
        self.debug = debug

        if self.debug : 
            print('=== Init ===')
            print(f'Image of size ({self.width}, {self.height})')

        if type(arr[0][0]) != tuple :
            self.color_type = 0

        nbe = len(list(arr[0][0]))

        if nbe == 2 : 
            self.color_type = 4 
        elif nbe == 3 : # 3 or 4 
            if self._should_use_palette() :
                self.color_type = 3
            else :
                self.color_type = 2
        elif nbe == 4 :
            if self._should_use_palette() :
                self.color_type = 3
            else : 
                self.color_type = 6
        if self.debug :
            print(f'Using color type : {self.color_type}')
            print(f'With Palette: {self.palette}')



    def _get_signature(self) :
        return b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'

    def _get_chunk(self, chunk_type, content) :
        len_part = self.to_bytes(len(content), 4)
        type_part = bytes(chunk_type, 'ascii')    

        crc_part = self.to_bytes(zlib.crc32(type_part + content), 4)
        if self.debug :
            print(f'New chunk {chunk_type} of size : {len(content)}')
        return len_part + type_part + content + crc_part

    def _get_iend_chunk(self) :
        return self._get_chunk('IEND', b'')


    def _get_ihdr_chunk(self) :
        if self.debug :
            print('=== IHDR chunk ===')
        w = self.to_bytes(self.width, 4)
        h = self.to_bytes(self.height, 4)

        bit_depth = b'\x08'
        color_type = self.to_bytes(self.color_type, 1) # Gray
        compression = b'\x00'
        filtering = b'\x00'
        loading = b'\x00' # Entrelacage ????

        if self.debug :
            print(f'With bit depth : {bit_depth}')
            print(f'With compression : {compression}')
            print(f'With filtering : {filtering}')
            print(f'With loading : {loading}')


        content = w + h + bit_depth + color_type + compression + filtering + loading

        return self._get_chunk('IHDR', content)


    def to_bytes(self, n, i) :
        return n.to_bytes(i, byteorder='big')


    def _get_idat_chunk(self) :
        # max size of 65535
        if self.debug :
            print('=== IDAT chunk ===')

        l = min(64, len(self.idat_content) - self.idat_index) 
        

        # XXXX XYYZ : 
        # Z = last block, 
        # YY = compression :00 for none, 01 for fixed huffman compression, 10 dynamic huffman compression, 11 reserved for errors
        # XXXXX Unknown
        # last_block = b'\x01' if self.idat_index+l == len(self.idat_content) else b'\x00'
        # Edit: actually last_block used in general IDAT content not specific IDAT chunk so of course it's the last one since that's always the only one.....

        if self.debug :
            print(f'Creating'+ (' last' if l + self.idat_index == len(self.idat_content) else ''), 'IDAT chunk')
            print(f'With size : {l}')
            # print(f'With cmf flag : {cmf_flg}')
        data = self.idat_content[self.idat_index: self.idat_index+l] 
        content =data #cmf_flg + last_block + data 

        self.idat_index += l
        return self._get_chunk('IDAT', content)

    def _get_idat_content(self, plte) :
        if self.debug :
            print(f'Getting IDAT contents')
        cmf = 8
        fill = 31 - ((cmf * 2 ** 8) % 31)
        cmf_flg = self.to_bytes(cmf * 2**8 + fill, 2)

        data = b''

        for scanline in self.data :
            curr = b'\x00'
            for e in scanline :
                if not plte :
                    if type(e) == tuple :
                        for v in e :
                            curr += self.to_bytes(v, 1)
                    else :
                        curr += self.to_bytes(e, 1)
                else :
                    curr += self.to_bytes(self.palette[e], 1)
            data += curr

        l = len(data)
        print(l)
        nlen = ones_complement(l, 16).to_bytes(2, byteorder='little')
        content = cmf_flg + b'\x01' +  l.to_bytes(2, byteorder='little') + nlen + data + zlib.adler32(data).to_bytes(4, byteorder='big')

        if self.debug :
            print(f'IDAT content: {len(content)}')
        return content

    def _get_idat_chunks(self, plte=False) :
        self.idat_index = 0
        self.idat_content = self._get_idat_content(plte)

        content = b''
        while self.idat_index < len(self.idat_content) :
        
            content += self._get_idat_chunk()

        return content
    def _get_plte_chunk(self) :
        if self.debug :
            print('=== PLTE chunk ===')
            print(f'With palette : {self.palette}')
        content = b''
        for pixel in self.palette.keys() :
            if type(pixel) != tuple :
                content += self.to_bytes(pixel, 1)
            else : 
                p = pixel[:-1] if len(pixel) == 4 else pixel
                for c in p :
                    content += self.to_bytes(c, 1)

        return self._get_chunk('PLTE', content)

    def _get_trns_chunk(self) :
        if self.debug :
            print('=== TRNS chunk ===')
        content = b''
        if self.palette == None :
            for line in self.data :
                for pixel in line :
                    content += self.to_bytes(pixel[-1], 1 if self.color_type == 3 else 2)
        else :
            for key in self.palette.keys() :
                content += self.to_bytes(key[-1], 1 if self.color_type == 3 else 2)


        return self._get_chunk('tRNS', content)



    def _should_use_palette(self) :
        palette = set()
        for line in self.data :
            for pixel in line :
                palette.add(pixel)

        if len(palette) > 256 :
            if self.debug :
                print(f'Should not use palette : {len(palette)} > 256')
            return False

        self.palette = {e:i for i,e in enumerate(list(palette))}
        return True

    def _should_use_trns(self) :
        if self.color_type in [4, 6] :
            return False

        if self.color_type in [2, 3] and len(self.data[0][0]) == 4 :
            return True
        
        return False


    def _get_content(self) :
        content = self._get_signature() + self._get_ihdr_chunk() 

        if self.color_type in [0, 4] :
            return content + self._get_idat_chunk() + self._get_iend_chunk()
         

        if self.palette != None : 
            content += self._get_plte_chunk()
            
        if self._should_use_trns() :
            content += self._get_trns_chunk() 
        content += self._get_idat_chunks(self.palette != None) 

        return content + self._get_iend_chunk()


    def save(self, name) :
        with open(name, 'wb') as f :
            f.write(self._get_content())



# Bibliography
# http://www.libpng.org/pub/png/spec/1.2/PNG-Chunks.html
# https://zestedesavoir.com/billets/4045/faconner-un-fichier-png-a-la-main/#fn-3-Q0xZuxCOUu
# https://fr.wikipedia.org/wiki/Portable_Network_Graphics
# Inspector : https://www.nayuki.io/page/png-file-chunk-inspector
# Filters : http://www.libpng.org/pub/png/spec/1.2/PNG-Filters.html
