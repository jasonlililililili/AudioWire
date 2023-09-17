import pyaudio
import numpy
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
wire1 = None
bose_volume = 100
jbl_volume = 100
bose_latency = 0.25
jbl_latency = 0

def audio_datalist_set_volume(datalist, volume):
    """ Change value of list of audio chunks """
    sound_level = (volume / 100.)

    chunk = numpy.frombuffer(datalist, numpy.int16)

    chunk = (chunk * sound_level)

    chunkBytes = chunk.astype(numpy.int16).tobytes()
    return chunkBytes

databuffer = bytearray()

try:
    p = pyaudio.PyAudio()
    bose_device_id = jbl_device_id = 0

    for idx in range(p.get_device_count()):
        d = p.get_device_info_by_index(idx)
        name = d.get('name').lower()
        if "bose" in name and bose_device_id == 0:
            bose_device_id = idx
        elif "jbl" in name and jbl_device_id == 0:
            jbl_device_id = idx
    mix = 0
    jbl_progress = 0    # use it directly, update it by +4*CHUNK
    bose_progress = 0    # use it directly, update it by +4*CHUNK
    
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if ( 'Line 1' in dev['name'] and dev['hostApi'] == 0 and dev['maxInputChannels'] > 0):
            mix = dev['index']
            print('dev_index', mix)

    wire1 = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index = mix,
                    frames_per_buffer=CHUNK)
    
    def jbl_callback(in_data, frame_count, time_info, status):
        global jbl_progress, jbl_latency
        if jbl_latency > 0:
            jbl_latency -= (frame_count/RATE)
            return (bytes(bytearray(frame_count*4)), pyaudio.paContinue)
        data = databuffer[jbl_progress:jbl_progress+4*frame_count]
        # print(jbl_progress)
        data = audio_datalist_set_volume(data, jbl_volume)
        jbl_progress += 4*frame_count
        return (data, pyaudio.paContinue)

    def bose_callback(in_data, frame_count, time_info, status):
        global bose_progress, bose_latency
        if bose_latency > 0:
            bose_latency -= (frame_count/RATE)
            return (bytes(bytearray(frame_count*4)), pyaudio.paContinue)
        data = databuffer[bose_progress:bose_progress+4*frame_count]
        data = audio_datalist_set_volume(data, bose_volume)
        bose_progress += 4*frame_count
        return (data, pyaudio.paContinue)
    
    bose = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True,
                output_device_index=bose_device_id,
                stream_callback=bose_callback)
    
    jbl = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    output=True,
                    output_device_index=jbl_device_id,
                    stream_callback=jbl_callback)

    while True:
        databuffer.extend(wire1.read(CHUNK))


except:
    if wire1 is not None:
        wire1.close()