import unittest
from common import fixture
from twine_edge_overlap.domain.model import Node,Document,Metrics,Result


class ModelTests(unittest.TestCase):
    def test_invalid_coordinates_and_counts(self):
        for number in (float('nan'),float('inf'),1e8):
            with self.subTest(number=number),self.assertRaises(ValueError): Node('A',number,0,100,100)
        for values in ((-1,0,0),(True,0,0),(0.,0,0)):
            with self.subTest(values=values),self.assertRaises(ValueError): Metrics(*values)

    def test_document_identity_and_patch_ranges_are_invariants(self):
        n=Node('A',1,1,100,100)
        invalid=[(b'abc',(n,n),(),((0,1),(1,2))),
                 (b'abc',(n,),(('A','missing'),),((0,1),)),
                 (b'abc',(n,),(),((0,9),)),
                 (b'abc',(n,),(),())]
        for values in invalid:
            with self.subTest(values=values),self.assertRaises(ValueError): Document(*values)

    def test_failure_cannot_have_valid_output(self):
        with self.assertRaises(ValueError): Result('falha','output.twee',None,None,'error')
