import unittest

from app.services.life_integration.contracts import ContextRestoreRequest, can_restore


class Phase15LifeIntegrationContractTests(unittest.TestCase):
    def test_restore_requires_owner_requester_and_scope(self):
        request = ContextRestoreRequest(
            owner_id="owner-1",
            requested_by_user="owner-1",
            scope="reading",
        )
        self.assertTrue(can_restore(request))

    def test_missing_scope_fails_closed(self):
        request = ContextRestoreRequest(
            owner_id="owner-1",
            requested_by_user="owner-1",
            scope="",
        )
        self.assertFalse(can_restore(request))

    def test_requester_mismatch_fails_closed(self):
        request = ContextRestoreRequest(
            owner_id="owner-1",
            requested_by_user="other-user",
            scope="reading",
        )
        self.assertFalse(can_restore(request))


if __name__ == "__main__":
    unittest.main()
