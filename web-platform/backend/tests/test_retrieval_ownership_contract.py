import inspect
import unittest

from app.routers.brain_advanced import (
    contradiction_candidates,
    export_brain_vault,
    hybrid_retrieval,
    review_contradiction,
)


class RetrievalOwnershipContractTests(unittest.TestCase):
    def test_hybrid_retrieval_sql_is_owner_scoped(self):
        source = inspect.getsource(hybrid_retrieval)
        self.assertIn("JOIN books b ON b.id = ch.book_id", source)
        self.assertGreaterEqual(source.count("AND b.owner_id = %s"), 1)
        self.assertIn(
            "query_vector, query_vector, owner_id, payload.limit,",
            source,
        )
        self.assertIn(
            "owner_id, payload.query, payload.query, payload.query, payload.limit,",
            source,
        )

    def test_export_is_owner_scoped(self):
        source = inspect.getsource(export_brain_vault)
        self.assertIn("WHERE owner_id=%s", source)
        self.assertIn("WHERE book_id = ANY(%s)", source)
        self.assertIn("c1.owner_id=%s AND c2.owner_id=%s", source)

    def test_contradiction_flows_are_owner_scoped(self):
        candidates = inspect.getsource(contradiction_candidates)
        review = inspect.getsource(review_contradiction)
        self.assertIn("JOIN books ba ON ba.id = cha.book_id", candidates)
        self.assertIn("WHERE ba.owner_id=%s AND bb.owner_id=%s", candidates)
        self.assertIn("lb.owner_id=%s", review)
        self.assertIn("rb.owner_id=%s", review)


if __name__ == "__main__":
    unittest.main()
