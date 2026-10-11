import os
import unittest
import numpy as np

os.environ.pop('OPENAI_API_KEY', None)

class PipelineTests(unittest.TestCase):
    def test_import_without_credentials(self):
        import pipeline
        self.assertTrue(callable(pipeline.match_user))

    def test_equal_scores_are_not_perfect_matches(self):
        from pipeline import match_user
        result = match_user(np.array([1., 0.]), np.array([[1., 1.], [1., 1.]]))
        self.assertEqual([score for _, score in result], [50., 50.])

    def test_invalid_vectors_have_actionable_error(self):
        from pipeline import match_user
        with self.assertRaisesRegex(ValueError, '維度'):
            match_user(np.ones(3), np.ones((2, 2)))

    def test_zero_vector_rejected(self):
        from pipeline import match_user
        with self.assertRaisesRegex(ValueError, '零向量'):
            match_user(np.zeros(2), np.ones((2, 2)))

    def test_ranking_is_stable_and_bounded(self):
        from pipeline import match_user
        self.assertEqual(match_user(np.array([1., 0.]), np.array([[0., 1.], [1., 0.], [-1., 0.]]), 2), [(1, 100.), (0, 50.)])

if __name__ == '__main__':
    unittest.main()
