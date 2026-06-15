"""Tests de Ola 4: planes, límites, top-up y webhook de MercadoPago."""
import pytest
from datetime import datetime, timezone
from proyecto_maria.services import billing_service
from proyecto_maria.database.models import User


class FakeUser:
    def __init__(self, plan="premium", billing_status="trial", used=0, extra=0):
        self.plan = plan
        self.billing_status = billing_status
        self.ops_used_this_period = used
        self.extra_ops_remaining = extra


def test_premium_plan_limit_enforced():
    u = FakeUser(plan="premium", used=10)
    ok, reason = billing_service.can_create_operation(u)
    assert not ok
    assert "límite" in reason.lower()


def test_premium_with_extra_credit_allows():
    u = FakeUser(plan="premium", used=10, extra=1)
    ok, reason = billing_service.can_create_operation(u)
    assert ok is True
    assert reason is None


def test_premium_within_limit_allows():
    u = FakeUser(plan="premium", used=9)
    ok, reason = billing_service.can_create_operation(u)
    assert ok is True


def test_record_operation_consumed_extra_credit():
    u = FakeUser(plan="premium", used=10, extra=2)
    billing_service.record_operation_created(u)
    assert u.ops_used_this_period == 11
    assert u.extra_ops_remaining == 1


def test_trial_without_billing_blocked():
    u = FakeUser(billing_status="none")
    ok, reason = billing_service.can_create_operation(u)
    assert not ok
    assert "suscripción" in reason.lower()


def test_get_plan_unknown_raises():
    with pytest.raises(ValueError, match="no disponible"):
        billing_service.get_plan("enterprise")


def test_plans_public_has_premium():
    plans = billing_service.plans_public()
    ids = {p["id"] for p in plans}
    assert "premium" in ids
    for p in plans:
        assert "price" in p
        assert "ops" in p


def test_webhook_payment_parses_subscription():
    payment = {
        "id": "123",
        "status": "approved",
        "external_reference": "alice:premium",
        "payer": {"id": "payer-1"},
        "card": {"last_four_digits": "1234", "payment_method": {"name": "visa"}},
    }
    update = billing_service.process_payment(payment)
    assert update is not None
    assert update["action"] == "subscription"
    assert update["plan"] == "premium"
    assert update["username"] == "alice"


def test_webhook_payment_parses_topup():
    payment = {
        "id": "456",
        "status": "approved",
        "external_reference": "bob:topup",
        "payer": {"id": "payer-2"},
    }
    update = billing_service.process_payment(payment)
    assert update is not None
    assert update["action"] == "topup"
    assert update["extra_ops_remaining"] == 10


def test_webhook_payment_404_unknown_reference():
    payment = {
        "id": "789",
        "status": "approved",
        "external_reference": "bad",
        "payer": {"id": "payer-3"},
    }
    assert billing_service.process_payment(payment) is None


def test_webhook_payment_pending_ignored():
    payment = {
        "id": "999",
        "status": "pending",
        "external_reference": "alice:premium",
        "payer": {"id": "payer-1"},
    }
    assert billing_service.process_payment(payment) is None
