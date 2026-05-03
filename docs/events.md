# Events

Canonical event schemas published over RabbitMQ. All events extend
`messaging.EventEnvelope` (`libs/messaging/src/messaging/envelope.py`).

TODO: document each `event_type` (`transaction.created`,
`bankmarket.purchase`, …) with its `payload` shape.
