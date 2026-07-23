import logging

_logger = logging.getLogger(__name__)


def _setup_mike_membership(env):
    """Create Mike Muscle's paid membership invoice after module install."""
    Partner = env["res.partner"]
    Invoice = env["account.move"]
    PaymentRegister = env["account.payment.register"]

    mike = Partner.search([("name", "=", "Mike Muscle")], limit=1)
    if not mike:
        _logger.warning("Mike Muscle partner not found, skipping demo setup")
        return

    gold_product = env["product.product"].search(
        [("product_tmpl_id.name", "=", "Annual gym workout plan")], limit=1
    )
    if not gold_product:
        _logger.warning("Annual gym workout plan product not found, skipping demo setup")
        return

    # Skip if an invoice already exists for this partner (idempotent)
    existing = Invoice.search(
        [
            ("partner_id", "=", mike.id),
            ("move_type", "=", "out_invoice"),
        ],
        limit=1,
    )
    if existing:
        _logger.info("Mike Muscle invoice %s already exists, skipping", existing.name)
        return

    invoice = Invoice.create(
        {
            "partner_id": mike.id,
            "move_type": "out_invoice",
            "invoice_date": "2026-07-21",
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": gold_product.id,
                        "quantity": 1,
                        "price_unit": 100.0,
                    },
                )
            ],
        }
    )
    invoice.action_post()

    receivable_line = env["account.move.line"].search(
        [
            ("move_id", "=", invoice.id),
            ("account_id.account_type", "=", "asset_receivable"),
        ],
        limit=1,
    )
    if not receivable_line:
        _logger.warning("No receivable line found for Mike's invoice")
        return

    cash_journal = env["account.journal"].search([("type", "=", "cash")], limit=1)

    # Use the actual invoice total (includes tax) for full payment
    wizard = PaymentRegister.create(
        {
            "payment_type": "inbound",
            "partner_type": "customer",
            "partner_id": mike.id,
            "amount": invoice.amount_total,
            "payment_date": "2026-07-21",
            "journal_id": cash_journal.id,
            "line_ids": [(6, 0, receivable_line.ids)],
        }
    )
    wizard.action_create_payments()

    invoice.invalidate_recordset(["payment_state"])
    _logger.info(
        "Mike Muscle membership invoice %s created and paid (%s)",
        invoice.name,
        invoice.payment_state,
    )
