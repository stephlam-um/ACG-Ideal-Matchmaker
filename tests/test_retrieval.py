import unittest
import numpy as np
from pipeline import match_user

class RetrievalTests(unittest.TestCase):
    def test_prepared_index_matches_reference(self):
        from retrieval import CosineIndex
        rng=np.random.default_rng(7)
        vectors=rng.normal(size=(50,32))
        query=rng.normal(size=32)
        expected=match_user(query,vectors,5)
        actual=CosineIndex(vectors).search(query,5)
        self.assertEqual([i for i,_ in actual],[i for i,_ in expected])
        np.testing.assert_allclose([s for _,s in actual],[s for _,s in expected],atol=1e-10)

    def test_index_owns_immutable_snapshot(self):
        from retrieval import CosineIndex
        vectors=np.array([[1.,0.],[0.,1.]])
        index=CosineIndex(vectors)
        vectors[:]=0
        self.assertEqual(index.search(np.array([1.,0.]),1),[(0,100.)])

    def test_trait_search_favors_distinctive_overlap(self):
        from retrieval import TraitIndex
        index=TraitIndex([{'moe_traits':['溫柔','偵探']},{'moe_traits':['溫柔','開朗']},{'moe_traits':['溫柔']}])
        self.assertEqual(index.search(['偵探','溫柔'],1)[0][0],0)

    def test_trait_search_no_match_is_empty(self):
        from retrieval import TraitIndex
        self.assertEqual(TraitIndex([{'moe_traits':['溫柔']}]).search(['冷靜'],5),[])

    def test_recall_uses_all_relevant_items(self):
        from evaluation import recall_at_k
        self.assertEqual(recall_at_k([1,2,3,4,5],[2,5,9],5),2/3)

    def test_random_baseline_samples_without_replacement(self):
        from evaluation import random_ranking
        self.assertEqual(len(set(random_ranking(50,5,np.random.default_rng(1)))),5)
