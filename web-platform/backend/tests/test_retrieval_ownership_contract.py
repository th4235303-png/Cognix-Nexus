import inspect
import unittest

from app.routers.brain_advanced import hybrid_retrieval


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


if __name__ == "__main__":
    unittest.main()
