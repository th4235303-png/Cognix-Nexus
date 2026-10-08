import unittest

from app.services.life_integration.contracts import ContextRestoreRequest, can_restore


class Phase15LifeIntegrationContractTests(unittest.TestCase):
    def test_restore_requires_owner_requester_and_scope(self):
        request = ContextRestoreRequest(
            id="restore-1",
            owner_id="owner-1",
            requested_by_user=True,
            scope=("reading",),
            reason="resume reading",
        )
        self.assertTrue(can_restore(request))

    def test_missing_scope_fails_closed(self):
        request = ContextRestoreRequest(
            id="restore-1",
            owner_id="owner-1",
            requested_by_user=True,
            scope=(),
            reason="resume reading",
        )
        self.assertFalse(can_restore(request))

    def test_unrequested_restore_fails_closed(self):
        request = ContextRestoreRequest(
            id="restore-1",
            owner_id="owner-1",
            requested_by_user=False,
            scope=("reading",),
            reason="ambient restore",
        )
        self.assertFalse(can_restore(request))


if __name__ == "__main__":
    unittest.main()
