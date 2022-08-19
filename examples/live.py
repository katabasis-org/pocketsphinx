#!/usr/bin/env python3
"""
Segment live speech from the default audio device.
"""

from pocketsphinx5 import Vad, Decoder
from collections import deque
import subprocess
import sys
import os

MODELDIR = os.path.join(os.path.dirname(__file__), os.path.pardir, "model")


class Endpointer(Vad):
    def __init__(
        self,
        stream=None,
        vad_frames=10,
        vad_mode=Vad.LOOSE,
        sample_rate=Vad.DEFAULT_SAMPLE_RATE,
        frame_length=Vad.DEFAULT_FRAME_LENGTH,
    ):
        super(Endpointer, self).__init__(vad_mode, sample_rate, frame_length)
        self.buf = deque(maxlen=vad_frames)
        if stream is not None:
            self.listen(stream)

    def listen(self, stream):
        self.buf.clear()
        self.stream = stream
        self.timestamp = 0.0
        self.start_time = self.end_time = None

    def read_frame(self):
        frame = self.stream.read(self.frame_bytes)
        self.buf.append((self.is_speech(frame), self.timestamp, frame))
        self.timestamp += self.frame_length
        return sum(f[0] for f in self.buf)

    def start(self):
        while True:
            speech_count = self.read_frame()
            if speech_count > 0.9 * self.buf.maxlen:
                self.start_time = self.buf[0][1]
                self.end_time = None
                return self.start_time

    def speech(self):
        while True:
            yield self.buf.popleft()
            speech_count = self.read_frame()
            if speech_count < 0.1 * self.buf.maxlen:
                self.end_time = self.buf[-1][1]
                for frame in self.buf:
                    yield frame
                self.buf.clear()
                break


def main():
    ep = Endpointer()
    decoder = Decoder(
        hmm=os.path.join(MODELDIR, "en-us/en-us"),
        lm=os.path.join(MODELDIR, "en-us/en-us.lm.bin"),
        dict=os.path.join(MODELDIR, "en-us/cmudict-en-us.dict"),
        samprate=float(ep.sample_rate),
    )
    soxcmd = f"sox -q -r {ep.sample_rate} -c 1 -b 16 -e signed-integer -d -t raw -"
    sox = subprocess.Popen(soxcmd.split(), stdout=subprocess.PIPE)
    ep.listen(sox.stdout)
    while True:
        start_time = ep.start()
        print("Speech start at %.2f" % (start_time), file=sys.stderr)
        decoder.start_utt()
        for is_speech, timestamp, frame in ep.speech():
            decoder.process_raw(frame)
            hyp = decoder.hyp()
            if hyp is not None:
                print("PARTIAL RESULT:", hyp.hypstr, file=sys.stderr)
        print("Speech end at %.2f" % (ep.end_time), file=sys.stderr)
        decoder.end_utt()
        print(decoder.hyp().hypstr)


try:
    main()
except KeyboardInterrupt:
    pass
