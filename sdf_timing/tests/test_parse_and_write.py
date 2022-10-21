# Copyright 2022 Tomas Brabec
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import os
import sys
import re
from io import StringIO

# add `sdf_timing` source tree into PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sdf_timing import sdfparse, sdfyacc, sdflex, sdfwrite
from ply import yacc
from .test_syntax_elements import NullLogger, reconfigure, parse


# Defines a data set to be tested. The structure is a list of records,
# where each record is a 3-element list such that 1st element is a description,
# 2nd element is the input (SDF) data and 3rd element is the expected data
# (i.e. SDF after parsing and writing out).
# Hence::
#
#     [ [<desc>, <intput>, <expected>], [<desc>, <intput>, <expected>], ...]
#
# Leading whitespace, trailing whitespace and empty lines are trimmed from
# the expected data before comparison with actuals (to make comparison more
# accurate).
testdata = [
['minimum_sdf',
'''(DELAYFILE (SDFVERSION "3.0"))''',
'''\
(DELAYFILE
  (SDFVERSION "3.0")
)
'''
],
['comment',
'''\
(DELAYFILE
  // some comment
  (SDFVERSION "3.0")
)''','''\
(DELAYFILE
  (SDFVERSION "3.0")
)'''
],
['full header',
'''\
(DELAYFILE
(SDFVERSION "3.0")
(DESIGN "BIGCHIP")
(DATE "March 12, 1995 09:46")
(VENDOR "Southwestern ASIC")
(PROGRAM "Fast program")
(VERSION "1.2a")
(DIVIDER /)
(VOLTAGE 5.5:5.0:4.5)
(PROCESS "best:nom:worst")
(TEMPERATURE -40:25:125)
(TIMESCALE 100 ps)
)''','''\
(DELAYFILE
(SDFVERSION "3.0")
(DESIGN "BIGCHIP")
(DATE "March 12, 1995 09:46")
(VENDOR "Southwestern ASIC")
(PROGRAM "Fast program")
(VERSION "1.2a")
(DIVIDER /)
(VOLTAGE 5.5:5:4.5)
(PROCESS "best:nom:worst")
(TEMPERATURE -40:25:125)
(TIMESCALE 100 ps)
)'''
],
['conditional delays',
'''\
(DELAYFILE
	(SDFVERSION "2.1")
	(TIMESCALE 1 ps)

	(CELL
	(CELLTYPE "routing_bel")
	(INSTANCE slicem/lut_c)
    (DELAY
	  (ABSOLUTE
	    (COND B==1'b0&&C==1'b0&&D==1'b0 (IOPATH A Z  (61.500:100.000:150.900) (26.900:40.000:61.400)))
	    (COND A==1'b0&&C==1'b0&&D==1'b0 (IOPATH B Z  (58.900:95.100:141.900) (24.500:36.000:55.800)))
	    (COND A==1'b0&&B==1'b0&&D==1'b0 (IOPATH C Z  (59.900:95.600:141.100) (24.200:35.200:55.000)))
	    (COND A==1'b0&&B==1'b0&&C==1'b0 (IOPATH D Z  (62.700:100.900:149.700) (26.100:38.300:59.900)))
	  )
    )
	)
)
''','''\
(DELAYFILE
(SDFVERSION "2.1")
(TIMESCALE 1 ps)
(CELL
  (CELLTYPE "routing_bel")
  (INSTANCE slicem/lut_c)
  (DELAY
    (ABSOLUTE
      (COND B == 1'b0 && C == 1'b0 && D == 1'b0 (IOPATH A Z (61.5:100:150.9)(26.9:40:61.4)))
      (COND A == 1'b0 && C == 1'b0 && D == 1'b0 (IOPATH B Z (58.9:95.1:141.9)(24.5:36:55.8)))
      (COND A == 1'b0 && B == 1'b0 && D == 1'b0 (IOPATH C Z (59.9:95.6:141.1)(24.2:35.2:55)))
      (COND A == 1'b0 && B == 1'b0 && C == 1'b0 (IOPATH D Z (62.7:100.9:149.7)(26.1:38.3:59.9)))
    )
  )
)
)'''
],
['real tripple',
'''\
(DELAYFILE
    (SDFVERSION "3.0")
    (TIMESCALE 1ps)

    (CELL
        (CELLTYPE "MY_CELL")
        (INSTANCE MY_INST)
        (DELAY
            (ABSOLUTE
                (IOPATH A O (1:2:3)(4:5:6)(7:8:9))
                (IOPATH B O (1:2:3)(4:5:6))
                (IOPATH C O (1:2:3)())
                (IOPATH D O (1:2:3))
                (IOPATH E O (1) () (3))
                (IOPATH F O () () ())
            )
        )
    )
)
''','''\
(DELAYFILE
(SDFVERSION "3.0")
(TIMESCALE 1 ps)
(CELL
  (CELLTYPE "MY_CELL")
  (INSTANCE MY_INST)
  (DELAY
    (ABSOLUTE
      (IOPATH A O (1:2:3)(4:5:6)(7:8:9))
      (IOPATH B O (1:2:3)(4:5:6))
      (IOPATH C O (1:2:3)())
      (IOPATH D O (1:2:3))
      (IOPATH E O (1)()(3))
      (IOPATH F O ()()())
    )
  )
)
)'''
],
['retain_path',
'''\
(DELAYFILE
  (SDFVERSION "3.0")
  (TIMESCALE 100 ps)
  (CELL
    (CELLTYPE "somecell")
    (INSTANCE someinst)
    (DELAY
      (ABSOLUTE
        (IOPATH mck b/c/clk (RETAIN (1)) (2))
        (COND en==1'b1 (IOPATH d[0] b/c/d (RETAIN (0.3)) (0.4:0.4:0.4)))
      )
    )
  )
)''',
'''\
(DELAYFILE
  (SDFVERSION "3.0")
  (TIMESCALE 100 ps)
  (CELL
    (CELLTYPE "somecell")
    (INSTANCE someinst)
    (DELAY
      (ABSOLUTE
        (IOPATH mck b/c/clk (RETAIN (1)) (2))
        (COND en == 1'b1 (IOPATH d[0] b/c/d (RETAIN (0.3)) (0.4:0.4:0.4)))
      )
    )
  )
)'''
],
];


# Removes empty lines and trims leading and trailing whitespace from
# a (generally multi-line) string.
def trim_whitespace(string):
    return "\n".join([l.strip() for l in string.splitlines() if l.strip()]);


# Performs full SDF syntax tests by parsing an input syntax, writing it
# out to a string buffer and comparing with the expected output.
class TestParseAndWrite(unittest.TestCase):

    def setUp(self):
        reconfigure(errorlog=NullLogger);
        self.buf = StringIO();
        self.maxDiff = None;

    def test_testdata(self):
        for data in testdata:
            with self.subTest( data[0], data = data ):
                exp = trim_whitespace( data[2] );
                sdf = parse( data[1] );
                self.buf.truncate(0);
                self.buf.seek(0);
                sdfwrite.print_sdf( sdf, channel=self.buf );
                act = trim_whitespace( self.buf.getvalue() );
                self.assertEqual( act, exp );

