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

# add `sdf_timing` source tree into PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sdf_timing import sdfparse, sdfyacc, sdflex
from ply import yacc

# Implements a "silent" PlyLogger. It is used to avoid various parser
# errors and warnings on unused grammer symbols, which would get reported
# once we start changing the parser's start symbol.
class NullLogger(yacc.PlyLogger):
    def debug(self, msg=None, *args, **kwargs):
        pass

    info = debug
    warning = debug
    error = debug

# Compiles a new parser with the given configuration.
#
# Unfortunately, `sdf_timing` current API supports no customization
# and, in genetral, is very stiff. Unless that changes, we do need
# to tap its internals for any customization.
def reconfigure(debug=False,write_tables=False,startsym=None, errorlog=None, debuglog=None):
    sdfyacc.parser = yacc.yacc(debug=debug, write_tables=write_tables, start=startsym, module=sdfyacc, errorlog=errorlog, debuglog=debuglog);
    sdfparse.init();

# Alternative implementation of `sdfparse.parse`. This implementation
# returns the output of PLY's parser (while `sdfparse.parse` compiles
# a custom structure representing an SDF file structure).
#
# As we are going to parse individual grammar/syntax elements, the parser
# output would not match the expected structure of `sdfparse.parse`, which
# would then return an empty result. Hence we need the output directly
# from the parser itself.
def parse(input):
    sdfparse.init()
    sdflex.input_data = input
    return sdfyacc.parser.parse(sdflex.input_data)


# Represents a delay value triplet.
#
# The class is primarily to provide common type operations like string
# conversion or equality operator.
class Delval:
    min = None;
    avg = None;
    max = None;
    all = None;

    def __init__(self, *args):
        if len(args)==1:
            if args[0] is None:
                pass
            elif type(args[0]) is list:
                # For a list type, we assume the value is to represent a triplet
                # and so make no guess that a list with a single element is to
                # represent an "all" scalar.
                self.min, self.avg, self.max, *ignore = args[0] + [None, None, None];
            elif type(args[0]) is dict:
                if 'all' in args[0]:
                    self.all = args[0]['all'];
                else:
                    self.min = args[0]['min'] if 'min' in args[0] else None;
                    self.avg = args[0]['avg'] if 'avg' in args[0] else None;
                    self.max = args[0]['max'] if 'max' in args[0] else None;
            elif type(args[0]) is str or not hasattr(args[0],'__len__'):
                self.all = args[0];
            else:
                raise TypeError()
        else:
            self.min, self.avg, self.max, *ignore = list(args) + [None, None, None];

    def __iter__(self):
        if self.all is None:
            return [self.min, self.avg, self.max];
        else:
            return [self.all];

    def __str__(self):
        if self.all is not None:
            return "(" + str(self.all) + ")";
        elif self.min is None and self.avg is None and self.max is None:
            return "()"

        return "(" + \
            ":".join([str(v) if v is not None else "" for v in [self.min, self.avg, self.max]]) + ")";

    def __eq__(self, other):
        if other is None:
            return self.isNone();
        elif isinstance(other, Delval):
            return self.all == other.all and self.min == other.min and self.avg == other.avg and self.max == other.max;
        elif type(other) is list:
            if self.all is not None:
                if len(other) == 1:
                    return self.all == other[0];
                else:
                    return [self.all, self.all, self.all] == other;
            else:
                return [self.min, self.avg, self.max] == other;
        elif type(other) is dict:
            if self.all is not None or self.isNone():
                if 'all' in other:
                    return {'all':self.all} == other;
                else:
                    return {'min':self.all, 'avg':self.all, 'max':self.all} == other;
            else:
                return {'min':self.min, 'avg':self.avg, 'max':self.max} == other;
        return False;

    def isNone(self):
        return  (self.all is None and self.min is None and self.avg is None and self.max is None);

# Represents a list of delay value triplets.
#
# The class is primarily to provide common type operations like string
# conversion, iteration or equality operator.
class DelvalList:

    def __init__(self, *args):
        self.delvals = [];
        for a in args:
            self.delvals.append( Delval(a) );

    def __iter__(self):
        return self.delvals.__iter__();

    def __str__(self):
        return "[" + ",".join([str(v) for v in self.delvals]) + "]";

    def __eq__(self,other):
        if type(other) is list and len(self.delvals) == len(other):
            for x,y in zip(self.delvals,other):
                if x != y: return False;
            return True;
        return False;


class TestSyntaxElements(unittest.TestCase):

    null_logger = None;

    # Compiles a delay dictionary from a triplet value.
    # We use this method for better maintence of changes in the SDF dictionary
    # key names.
    def compile_delay_triplet(self, triple):
        return {'min': triple[0], 'avg': triple[1], 'max': triple[2]};

    # Compiles a delay dictionary from a scalar delay value.
    # We use this method for better maintence of changes in the SDF dictionary
    # key names.
    def compile_delay_scalar(self, scalar):
        return {'all': scalar};

    def setUp(self):
        self.null_logger = NullLogger;

    #-------------------------------------
    # rvalue
    #-------------------------------------
    # [1] Open Verilog Internationa, Standard Delay Format Specification v3.0, May 1995
    #
    # From spec [1]:
    #
    #   Each rvalue is either a single `RNUMBER` or an `rtriple`, containing three
    #   `RNUMBER`s separated by colons, in parentheses.
    #
    #   Syntax
    #         rvalue ::= ( RNUMBER? )
    #                ||= ( rtriple? )
    #
    #   The use of single `RNUMBER`s and `rtriple`s should not be mixed in the same
    #   SDF file. All `RNUMBER`s can have negative, zero or positive values.
    #   The use of triples in SDF allows you to carry three sets of data in the same
    #   file. Each number in the triple is an alternative value for the data and is
    #   typically selected from the triple by the annotator or analysis tool on an
    #   instruction from the user. The prevailing use of the three numbers is to
    #   represent *minimum*, *typical* and *maximum* values computed at three
    #   process/operating conditions for the entire design. Any one or any two
    #   (but not all three) of the numbers in a triple may be omitted if the
    #   separating colons are left in place. This indicates that no value has been
    #   computed for that data, and the annotator should not make any changes if
    #   that number is selected from the triple. For absolute delays, this is not the
    #   same as entering a value of 0.0.
    #
    # `rvalue`s are used to define delay values, `delval`s. There is a note in `delval`
    # description that allows use of *empty* `rvalue`. From [1]:
    #
    #   ... Note that since any `rvalue`
    #   can be an empty pair of parentheses, each type of delay data can be
    #   annotated or omitted as the need arises.

    def test_rvalue_empty(self):
        data ='()'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        sdf = parse(data);
        exp = self.compile_delay_scalar( None );
        self.assertEqual( sdf, exp );

    def test_rvalue_triple_three_int_1(self):
        data ='(1:2:3)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        sdf = parse(data);
        exp = self.compile_delay_triplet( [1,2,3] );
        self.assertEqual( sdf, exp );

    def test_rvalue_triple_three_int_2(self):
        data ='(-1:0:1)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        sdf = parse(data);
        exp = self.compile_delay_triplet( [-1,0,1] );
        self.assertEqual( sdf, exp );

    def test_rvalue_triple_two_int_1(self):
        data ='(1:2:)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        sdf = parse(data);
        exp = self.compile_delay_triplet( [1,2,None] );
        self.assertEqual( sdf, exp );

    def test_rvalue_triple_two_int_2(self):
        data ='(1::3)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        sdf = parse(data);
        exp = self.compile_delay_triplet( [1,None,3] );
        self.assertEqual( sdf, exp );

    def test_rvalue_triple_two_int_3(self):
        data ='(:2:3)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        sdf = parse(data);
        exp = self.compile_delay_triplet( [None,2,3] );
        self.assertEqual( sdf, exp );

    def test_rvalue_triple_one_int_1(self):
        data ='(1::)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        sdf = parse(data);
        exp = self.compile_delay_triplet( [1,None,None] );
        self.assertEqual( sdf, exp );

    def test_rvalue_triple_one_int_2(self):
        data ='(:2:)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        sdf = parse(data);
        exp = self.compile_delay_triplet( [None,2,None] );
        self.assertEqual( sdf, exp );

    def test_rvalue_triple_one_int_3(self):
        data ='(::3)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        sdf = parse(data);
        exp = self.compile_delay_triplet( [None,None,3] );
        self.assertEqual( sdf, exp );

    def test_rvalue_triple_none(self):
        data ='(::)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        with self.assertRaises(Exception):
            sdf = parse(data);

    def test_rvalue_triple_missing_lpar(self):
        data ='1:2:3)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        with self.assertRaises(Exception):
            sdf = parse(data);

    def test_rvalue_triple_missing_rpar(self):
        data ='(1:2:3'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        with self.assertRaises(Exception):
            sdf = parse(data);

    def test_rvalue_triple_missing_doublecolon_1(self):
        data ='(1:23)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        with self.assertRaises(Exception):
            sdf = parse(data);

    def test_rvalue_triple_missing_doublecolon_2(self):
        data ='(12:3)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        with self.assertRaises(Exception):
            sdf = parse(data);

    def test_rvalue_single_int_1(self):
        data ='(123)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        sdf = parse(data);
        exp = self.compile_delay_scalar(123);
        self.assertEqual( sdf, exp );

    def test_rvalue_single_float_1(self):
        data ='(1.23)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        sdf = parse(data);
        exp = self.compile_delay_scalar(1.23);
        self.assertEqual( sdf, exp );

    #-------------------------------------
    # interconnect delay
    #-------------------------------------

    def test_interconnect_simple_1(self):
        data ='(INTERCONNECT a b (1:2:3))'
        reconfigure(startsym='interconnect', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'a', 'to_pin': 'b', 'type': 'interconnect'};
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );
        self.assertEqual( DelvalList([1,2,3]), sdf['delay_paths'] );

    def test_interconnect_simple_2(self):
        data ='(INTERCONNECT a/b/c e/f (1:2:3))'
        reconfigure(startsym='interconnect', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'a/b/c', 'to_pin': 'e/f', 'type': 'interconnect'};
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );
        self.assertEqual( DelvalList([1,2,3]), sdf['delay_paths'] );

    def test_interconnect_empty_delay(self):
        data ='(INTERCONNECT a b ())'
        reconfigure(startsym='interconnect', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'a', 'to_pin': 'b', 'type': 'interconnect'};
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );
        self.assertEqual( DelvalList(None), sdf['delay_paths'] );

    def test_interconnect_missing_port(self):
        data ='(INTERCONNECT a (1:2:3))'
        reconfigure(startsym='interconnect', errorlog=self.null_logger);
        with self.assertRaises(Exception):
            sdf = parse(data);

    def test_interconnect_missing_ports(self):
        data ='(INTERCONNECT (1:2:3))'
        reconfigure(startsym='interconnect', errorlog=self.null_logger);
        with self.assertRaises(Exception):
            sdf = parse(data);

    def test_interconnect_missing_delay(self):
        data ='(INTERCONNECT a b)'
        reconfigure(startsym='interconnect', errorlog=self.null_logger);
        with self.assertRaises(Exception):
            sdf = parse(data);

    def test_interconnect_missing_lpar(self):
        data ='INTERCONNECT a b (1:2:3))'
        reconfigure(startsym='interconnect', errorlog=self.null_logger);
        with self.assertRaises(Exception):
            sdf = parse(data);

    def test_interconnect_missing_rpar(self):
        data ='(INTERCONNECT a b (1:2:3)'
        reconfigure(startsym='interconnect', errorlog=self.null_logger);
        with self.assertRaises(Exception):
            sdf = parse(data);

    #-------------------------------------
    # conditional port expression
    #-------------------------------------

    def test_cond_path_expr_const_1(self):
        data ='1\'b0'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['1\'b0'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_const_2(self):
        data ='1\'b1'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['1\'b1'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_const_3(self):
        data ='1\'B0'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['1\'B0'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_const_4(self):
        data ='1\'B1'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['1\'B1'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_const_5(self):
        data ='\'b0'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['\'b0'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_const_6(self):
        data ='\'b1'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['\'b1'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_const_7(self):
        data ='\'B0'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['\'B0'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_const_8(self):
        data ='\'B1'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['\'B1'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_const_9(self):
        data ='0'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['0'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_const_10(self):
        data ='1'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['1'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_port_1(self):
        data ='a'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['a'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_port_2(self):
        data ='a/b/c'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['a/b/c'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_port_3(self):
        data ='a.b.c'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['a.b.c'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_unary_const_1(self):
        data ='~1\'b0'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['~', '1\'b0'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_unary_port_1(self):
        data ='~a/b/c'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['~', 'a/b/c'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_unary_port_2(self):
        data ='!x'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['!', 'x'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_binary_1(self):
        data ='a & b'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['a','&','b'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_binary_2(self):
        data ='a && 1\'b1'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['a','&&','1\'b1'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_binary_3(self):
        data ='1\'b0 | b'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['1\'b0','|','b'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_binary_4(self):
        data ='x || y'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['x','||','y'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_binary_5(self):
        data ='c.d ^ a/b'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['c.d','^','a/b'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_binary_6(self):
        data ='A==0'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['A','==','0'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_binary_7(self):
        data ='A!=C'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['A','!=','C'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_parenthesis_1(self):
        data ='(A)'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['(','A',')'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_parenthesis_2(self):
        data ='(1\'b1 && A)'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['(','1\'b1','&&','A',')'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_parenthesis_3(self):
        data ='(A&(B|C))'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['(','A','&','(','B','|','C',')',')'];
        self.assertEqual( act, exp );

    #-------------------------------------
    # conditional path delay
    #-------------------------------------
    # [1] Open Verilog Internationa, Standard Delay Format Specification v3.0, May 1995
    #
    # From spec [1]:
    #
    #   The `COND` keyword allows the specification of conditional (state-
    #   dependent) input-to-output path delays.
    #
    #   Syntax
    #
    #       ( COND QSTRING? conditional_port_expr
    #           ( IOPATH port_spec port_instance delval_list ) )
    #

    def test_cond_iopath_simple_1(self):
        data ='(COND b (IOPATH a y () ()))'
        reconfigure(startsym='cond_delay', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'a', 'to_pin': 'y', 'type': 'iopath', 'is_cond': True, 'cond_equation': 'b'};
        act = {k: sdf[0][k] for k in exp.keys()}; # !!! `sdf` is a list of paths
        self.assertEqual( act, exp );

    def test_cond_iopath_simple_2(self):
        data ='(COND x & ~y (IOPATH a y () ()))'
        reconfigure(startsym='cond_delay', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'a', 'to_pin': 'y', 'type': 'iopath', 'is_cond': True, 'cond_equation': 'x & ~ y'};
        act = {k: sdf[0][k] for k in exp.keys()}; # !!! `sdf` is a list of paths
        self.assertEqual( act, exp );

    def test_cond_iopath_six_vals(self):
        data = '''(COND PA==1'b0&&PB==1'b1&&PS==1'b1 (IOPATH EN PADM () () (0.661::0.682) (3.513::11.574) (0.945::0.964) (3.176::10.900)))'''
        reconfigure(startsym='cond_delay', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'EN', 'to_pin': 'PADM', 'type': 'iopath', 'is_cond': True, 'cond_equation': 'PA == 1\'b0 && PB == 1\'b1 && PS == 1\'b1'};
        act = {k: sdf[0][k] for k in exp.keys()}; # !!! `sdf` is a list of paths
        self.assertEqual( act, exp );


    #-------------------------------------
    # delay list
    #-------------------------------------

    def test_delay_list_1(self):
        data ='''
        (COND b & a (IOPATH a y () ()))
        (COND a | b (IOPATH a y () ()))
        '''
        reconfigure(startsym='delay_list', errorlog=self.null_logger);
        sdf = parse(data);
        exp = [
                {'from_pin': 'a', 'to_pin': 'y', 'type': 'iopath', 'is_cond': True, 'cond_equation': 'b & a'},
                {'from_pin': 'a', 'to_pin': 'y', 'type': 'iopath', 'is_cond': True, 'cond_equation': 'a | b'}
                ];
        act = [];
        for i in range(0,len(exp)):
            act.append( {k: sdf[i][k] for k in exp[i].keys()} );
        self.assertEqual( act, exp );


    #-------------------------------------
    # width check
    #-------------------------------------

    def test_tcheck_width_simple(self):
        data ='''(WIDTH clk (4.4:7.5:11.3))''';
        reconfigure(startsym='width_check', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'clk', 'to_pin': 'clk', 'type': 'width', 'is_timing_check': True, 'is_cond': False,
                'from_pin_edge': None, 'to_pin_edge': None};
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );
        # test delay value
        self.assertTrue( 'nominal' in sdf['delay_paths'] );
        self.assertEqual( Delval([4.4,7.5,11.3]), sdf['delay_paths']['nominal'] );

    def test_tcheck_width_port_negedge_spec(self):
        data ='''(WIDTH (negedge clk) (4.4:7.5:11.3))''';
        reconfigure(startsym='width_check', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'clk', 'to_pin': 'clk', 'type': 'width', 'is_timing_check': True, 'is_cond': False,
                'from_pin_edge': 'negedge', 'to_pin_edge': 'negedge'};
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );
        # test delay value
        self.assertTrue( 'nominal' in sdf['delay_paths'] );
        self.assertEqual( Delval([4.4,7.5,11.3]), sdf['delay_paths']['nominal'] );

    def test_tcheck_width_port_posedge_spec(self):
        data ='''(WIDTH (posedge path/to/rst) (11))''';
        reconfigure(startsym='width_check', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'path/to/rst', 'to_pin': 'path/to/rst', 'type': 'width', 'is_timing_check': True,
                'is_cond': False, 'from_pin_edge': 'posedge', 'to_pin_edge': 'posedge'};
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );
        # test delay value
        self.assertTrue( 'nominal' in sdf['delay_paths'] );
        self.assertEqual( Delval(11), sdf['delay_paths']['nominal'] );

    def test_tcheck_width_conditional(self):
        data ='''(WIDTH (COND ENABLE (posedge CP)) (1:1:1) )''';
        reconfigure(startsym='width_check', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'CP', 'to_pin': 'CP', 'type': 'width', 'is_timing_check': True, 'is_cond': True,
                'from_pin_edge': 'posedge', 'to_pin_edge': 'posedge', 'cond_equation': 'ENABLE'};
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );
        # test delay value
        self.assertTrue( 'nominal' in sdf['delay_paths'] );
        self.assertEqual( Delval(1,1,1), sdf['delay_paths']['nominal'] );


    #-------------------------------------
    # period check
    #-------------------------------------

    def test_tcheck_period_simple(self):
        data ='''(PERIOD clk (1::2))''';
        reconfigure(startsym='period_check', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'clk', 'to_pin': 'clk', 'type': 'period', 'is_timing_check': True, 'is_cond': False,
                'from_pin_edge': None, 'to_pin_edge': None};
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );
        # test delay value
        self.assertTrue( 'nominal' in sdf['delay_paths'] );
        self.assertEqual( Delval(1,None,2), sdf['delay_paths']['nominal'] );

    def test_tcheck_period_conditional(self):
        data ='''(PERIOD (COND a/b==1'b0 && !c (negedge clk)) (1))''';
        reconfigure(startsym='period_check', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'clk', 'to_pin': 'clk', 'type': 'period', 'is_timing_check': True, 'is_cond': True,
                'from_pin_edge': 'negedge', 'to_pin_edge': 'negedge', 'cond_equation': 'a/b == 1\'b0 && ! c'};
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );
        # test delay value
        self.assertTrue( 'nominal' in sdf['delay_paths'] );
        self.assertEqual( Delval(1), sdf['delay_paths']['nominal'] );

    def test_tcheck_period_port_posedge_spec(self):
        data ='''(PERIOD (posedge path/to/CK) ())''';
        reconfigure(startsym='period_check', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'path/to/CK', 'to_pin': 'path/to/CK', 'type': 'period', 'is_timing_check': True,
                'is_cond': False, 'from_pin_edge': 'posedge', 'to_pin_edge': 'posedge'};
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );
        # test delay value
        self.assertTrue( 'nominal' in sdf['delay_paths'] );
        self.assertEqual( Delval(None), sdf['delay_paths']['nominal'] );


    #-------------------------------------
    # nochange check
    #-------------------------------------

    def test_tcheck_nochange_simple(self):
        data ='''(NOCHANGE wr addr (:1:) (:2:))''';
        reconfigure(startsym='nochange_check', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'addr', 'to_pin': 'wr', 'type': 'nochange', 'is_timing_check': True, 'is_cond': False,
                'from_pin_edge': None, 'to_pin_edge': None};
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );
        # test delay values
        exp = {'setup': Delval(None,1,None), 'hold': Delval(None,2,None)};
        self.assertEqual( sdf['delay_paths'].keys(), exp.keys() );
        for k,v in exp.items():
            self.assertEqual( v, sdf['delay_paths'][k] );

    def test_tcheck_nochange_conditional_1st(self):
        data ='''(NOCHANGE (COND 1'b0 por) (posedge rst) (1) (2))''';
        reconfigure(startsym='nochange_check', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'rst', 'to_pin': 'por', 'type': 'nochange', 'is_timing_check': True, 'is_cond': True,
                'from_pin_edge': 'posedge', 'to_pin_edge': None, 'cond_equation': '1\'b0'};
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );
        # test delay value
        exp = {'setup': Delval(1), 'hold': Delval(2)};
        self.assertEqual( sdf['delay_paths'].keys(), exp.keys() );
        for k,v in exp.items():
            self.assertEqual( v, sdf['delay_paths'][k] );

    def test_tcheck_nochange_conditional_2nd(self):
        data ='''(NOCHANGE (negedge por) (COND a/b&c (posedge rst)) (1) (2))''';
        reconfigure(startsym='nochange_check', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'rst', 'to_pin': 'por', 'type': 'nochange', 'is_timing_check': True, 'is_cond': True,
                'from_pin_edge': 'posedge', 'to_pin_edge': 'negedge', 'cond_equation': 'a/b & c'};
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );
        # test delay value
        exp = {'setup': Delval(1), 'hold': Delval(2)};
        self.assertEqual( sdf['delay_paths'].keys(), exp.keys() );
        for k,v in exp.items():
            self.assertEqual( v, sdf['delay_paths'][k] );


    #-------------------------------------
    # pathconstraint
    #-------------------------------------

    def test_pathconstraint_simple(self):
        data ='''(PATHCONSTRAINT a y (9:10:11) (12:13:14))'''
        reconfigure(startsym='path_constraint', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'a', 'to_pin': 'y', 'type': 'pathconstraint',
                'is_timing_check': False, 'is_timing_env': True,
                'is_cond': False,'cond_equation': None,
                'from_pin_edge': None, 'to_pin_edge': None};
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );
        # test delay values
        exp = {'rise': Delval(9,10,11), 'fall': Delval(12,13,14)};
        self.assertEqual( sdf['delay_paths'].keys(), exp.keys() );
        for k,v in exp.items():
            self.assertEqual( v, sdf['delay_paths'][k] );


    #-------------------------------------
    # iopath
    #-------------------------------------

    def test_iopath_simple(self):
        data ='''(IOPATH a y (1:2:3))'''
        reconfigure(startsym='iopath', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'a', 'to_pin': 'y', 'type': 'iopath',
                'is_timing_check': False, 'is_timing_env': False,
                'is_cond': False,'cond_equation': None,
                'from_pin_edge': None, 'to_pin_edge': None,
                'has_retain': False};
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );
        self.assertEqual( DelvalList([1,2,3]), sdf['delay_paths'] );

    def test_iopath_retain_simple(self):
        data ='''(IOPATH a y (RETAIN (0:1:2)) (1:2:3))'''
        reconfigure(startsym='iopath', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'a', 'to_pin': 'y', 'type': 'iopath',
                'is_timing_check': False, 'is_timing_env': False,
                'is_cond': False,'cond_equation': None,
                'from_pin_edge': None, 'to_pin_edge': None,
                'has_retain': True};
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );
        self.assertEqual( DelvalList([1,2,3]), sdf['delay_paths'] );
        self.assertEqual( DelvalList([0,1,2]), sdf['retain_paths'] );


    #-------------------------------------
    # timingcheck
    #-------------------------------------

    def test_timingcheck_1(self):
        data ='''
        (TIMINGCHECK
        (SETUPHOLD d (posedge clk) (3:4:5) (-1:-1:-1))
        (WIDTH clk (4.4:7.5:11.3))
        )
        '''
        reconfigure(startsym='timing_check', errorlog=self.null_logger);
        sdf = parse(data);
        exp = [
                {'from_pin': 'clk', 'to_pin': 'd', 'type': 'setuphold', 'is_cond': False, 'cond_equation': None},
                {'from_pin': 'clk', 'to_pin': 'clk', 'type': 'width', 'is_cond': False, 'cond_equation': None}
                ];
        act = [];
        self.assertEqual( len(sdf), len(exp) );
        for i in range(0,len(exp)):
            act.append( {k: sdf[i][k] for k in exp[i].keys()} );
        self.assertEqual( act, exp );


    #-------------------------------------
    # delay (absolute)
    #-------------------------------------

    # empty absolute delay not supported by SDF grammar (as per SDF Std.)
    #TODO presently fails due to being allowed by the grammar
    @unittest.expectedFailure
    def test_delay_absolute_empty(self):
        data ='''(DELAY (ABSOLUTE))'''
        reconfigure(startsym='delay', errorlog=self.null_logger);
        with self.assertRaises(Exception):
            sdf = parse(data);

    def test_delay_absolute_1(self):
        data ='''
        (DELAY
        (ABSOLUTE
        (IOPATH a y (1.5:2.5:3.4) (2.5:3.6:4.7))
        (IOPATH b y (1.4:2.3:3.2) (2.3:3.4:4.3))
        )
        )
        '''
        reconfigure(startsym='delay', errorlog=self.null_logger);
        sdf = parse(data);
        exp = [
                {'from_pin': 'a', 'to_pin': 'y', 'type': 'iopath', 'is_cond': False, 'cond_equation': None},
                {'from_pin': 'b', 'to_pin': 'y', 'type': 'iopath', 'is_cond': False, 'cond_equation': None}
                ];
        act = [];
        self.assertEqual( len(sdf), len(exp) );
        for i in range(0,len(exp)):
            act.append( {k: sdf[i][k] for k in exp[i].keys()} );
        self.assertEqual( act, exp );


    #-------------------------------------
    # delay (incremental)
    #-------------------------------------

    # empty incremental delay not supported by SDF grammar (as per SDF Std.)
    def test_delay_increment_empty(self):
        data ='''(DELAY (INCREMENT))'''
        reconfigure(startsym='delay', errorlog=self.null_logger);
        with self.assertRaises(Exception):
            sdf = parse(data);


    #-------------------------------------
    # timingenv
    #-------------------------------------

    def test_timingenv_list(self):
        data ='''(TIMINGENV
        (PATHCONSTRAINT I2.H01 I1.N01 (989:1269:1269) (989:1269:1269))
        (PATHCONSTRAINT I2.H01 I3.N01 (904:1087:1087) (904:1087:1087))
        )'''
        reconfigure(startsym='timingenv', errorlog=self.null_logger);
        sdf = parse(data);
        exp = [
                {'from_pin': 'I2.H01', 'to_pin': 'I1.N01',
                    'type': 'pathconstraint', 'is_timing_env': True},
                {'from_pin': 'I2.H01', 'to_pin': 'I3.N01',
                    'type': 'pathconstraint', 'is_timing_env': True}
                ];
        act = [];
        self.assertEqual( len(sdf), len(exp) );
        for i in range(0,len(exp)):
            act.append( {k: sdf[i][k] for k in exp[i].keys()} );
        self.assertEqual( act, exp );

        # test delay values
        exp_delays = [
                {'rise': Delval(989,1269,1269), 'fall': Delval(989,1269,1269)},
                {'rise': Delval(904,1087,1087), 'fall': Delval(904,1087,1087)}
                ];
        for i in range(0,len(exp_delays)):
            self.assertEqual( sdf[i]['delay_paths'].keys(), exp_delays[i].keys() );
            for k,v in exp_delays[i].items():
                self.assertEqual( v, sdf[i]['delay_paths'].get(k) );


    #-------------------------------------
    # cell
    #-------------------------------------

    def test_cell_1(self):
        data ='''
        (CELL
            (CELLTYPE "AND2")
            (INSTANCE top/b/d)
            (DELAY
                (ABSOLUTE
                    (IOPATH a y (1.5:2.5:3.4)(2.5:3.6:4.7))
                    (IOPATH b y (1.4:2.3:3.2)(2.3:3.4:4.3))
                )
            )
        )
        '''
        reconfigure(startsym='cell', errorlog=self.null_logger);
        sdf = parse(data);
        self.assertEqual( sdf.keys(), {'cell','inst','delays'} );

        # test cell and instance name
        exp = { 'cell':'AND2', 'inst':'top/b/d' };
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );

        # test delay records
        exp = {
                "iopath_a_y": {
                    'from_pin': 'a', 'to_pin': 'y', 'type': 'iopath',
                    'is_cond': False, 'cond_equation': None
                    },
                "iopath_b_y": {
                    'from_pin': 'b', 'to_pin': 'y', 'type': 'iopath',
                    'is_cond': False, 'cond_equation': None
                    }
                };
        self.assertEqual( sdf['delays'].keys(), exp.keys() );

        act = {};
        for i in exp.keys():
            act.update( {i: {k: sdf['delays'][i].get(k) for k in exp[i].keys()}} );
        self.assertEqual( act, exp );

    # This test case exercises that there will be no aliasing
    # in keys of delays and timing constraints if they represent
    # a timing arc with same from-to pair of pins.
    def test_cell_timing_uniquification(self):
        data ='''
        (CELL
            (CELLTYPE "AND2")
            (INSTANCE top.b.d)
            (DELAY
                (ABSOLUTE
                    (IOPATH a y (1:2:3)(1:2:3))
                    (COND en (IOPATH a y (4:5:6)(4:5:6)))
                )
            )
        )
        '''
        reconfigure(startsym='cell', errorlog=self.null_logger);
        sdf = parse(data);
        self.assertEqual( sdf.keys(), {'cell','inst','delays'} );

        # test cell and instance name
        exp = { 'cell':'AND2', 'inst':'top.b.d' };
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );

        # test delay records
        exp = {
                "iopath_a_y": {
                    'from_pin': 'a', 'to_pin': 'y', 'type': 'iopath',
                    'is_cond': False, 'cond_equation': None
                    },
                "iopath_a_y#1": {
                    'from_pin': 'a', 'to_pin': 'y', 'type': 'iopath',
                    'is_cond': True, 'cond_equation': 'en'
                    }
                };
        self.assertEqual( sdf['delays'].keys(), exp.keys() );

        act = {};
        for i in exp.keys():
            act.update( {i: {k: sdf['delays'][i].get(k) for k in exp[i].keys()}} );
        self.assertEqual( act, exp );


    #-------------------------------------
    # header
    #-------------------------------------

    def test_header_full(self):
        data ='''
        (SDFVERSION "3.0")
        (DESIGN "testchip")
        (DATE "Dec 17, 1991 14:49:48")
        (VENDOR "Big Chips Inc.")
        (PROGRAM "Chip Analyzer")
        (VERSION "1.3b")
        (DIVIDER .)
        (VOLTAGE :3.8: )
        (PROCESS "worst")
        (TEMPERATURE : 37:)
        (TIMESCALE 10ps)
        '''
        reconfigure(startsym='sdf_header', errorlog=self.null_logger);
        sdf = parse(data);
        self.assertTrue( type(sdf) is dict );
        exp = {'sdfversion': '3.0', 'design': 'testchip',
                'date': 'Dec 17, 1991 14:49:48', 'vendor': 'Big Chips Inc.',
                'program': 'Chip Analyzer', 'version': '1.3b', 'divider': '.',
                'process': 'worst', 'timescale': '10ps',
                'voltage': {'min':None, 'avg':3.8, 'max':None},
                'temperature': {'min':None, 'avg':37, 'max':None}
                };
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );

    def test_header_minimal(self):
        data ='''
        (SDFVERSION "3.0")
        '''
        reconfigure(startsym='sdf_header', errorlog=self.null_logger);
        sdf = parse(data);
        self.assertTrue( type(sdf) is dict );
        exp = {'sdfversion': '3.0'};
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );

        ## import json;
        ## print( json.dumps(sdf, indent=2) );



if __name__ == '__main__':
    unittest.main()

