# -*- c-basic-offset: 4; indent-tabs-mode: nil -*- */
# ====================================================================
# Copyright (c) 2013 Carnegie Mellon University.  All rights
# reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer. 
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# This work was supported in part by funding from the Defense Advanced 
# Research Projects Agency and the National Science Foundation of the 
# United States of America, and the CMU Sphinx Speech Consortium.
#
# THIS SOFTWARE IS PROVIDED BY CARNEGIE MELLON UNIVERSITY ``AS IS'' AND 
# ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, 
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL CARNEGIE MELLON UNIVERSITY
# NOR ITS EMPLOYEES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT 
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, 
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY 
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# ====================================================================


from itertools import izip
from os import environ, path
from sys import stdout

from pocketsphinx import *
from sphinxbase import *

MODELDIR = "../../../model"
DATADIR = "../../../test/data"

# Create a decoder with certain model
config = Decoder.default_config()
config.set_string('-hmm', path.join(MODELDIR, 'hmm/en_US/hub4wsj_sc_8k'))
config.set_string('-lm', path.join(MODELDIR, 'lm/en/turtle.DMP'))
config.set_string('-dict', path.join(MODELDIR, 'lm/en/turtle.dic'))
decoder = Decoder(config)

# Decode with lm
decoder.decode_raw(open(path.join(DATADIR, 'goforward.raw'), 'rb'))
print 'Decoding with "turtle" language:', decoder.hyp().hypstr

# Switch to JSGF grammar
jsgf = Jsgf(path.join(DATADIR, 'goforward.gram'))
rule = jsgf.get_rule('<goforward.move2>')
fsg = jsgf.build_fsg(rule, decoder.get_logmath(), 7.5)
fsg.write(stdout)
fsg.writefile('goforward.fsg')

# Call update to switch to fsg search mode first
decoder.update_fsgset()

fsg_set = decoder.get_fsgset()
fsg_set.add("current", fsg)
fsg_set.select("current")
decoder.update_fsgset()

decoder.decode_raw(open(path.join(DATADIR, 'goforward.raw'), 'rb'))
print 'Decoding with "goforward" grammar:', decoder.hyp().hypstr