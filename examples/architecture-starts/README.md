# Architecture starting code

These small Python programs demonstrate one critical mechanism per project. They do not provision AWS or supply the completed service. Open the linked project for its scenario, interfaces, build sequence, infrastructure and observable outcomes.

Run a program from the repository root with `python3 examples/architecture-starts/<name>.py`. Python 3.12+; standard library only. Each uses local fixture data.

| Project | Starting program |
|---|---|
| [Bookmark service](../../curriculum/03-production/01-system-design/problems/bookmark-service.md) | [bookmark_service.py](bookmark_service.py) |
| [URL shortener: who owns the code?](../../curriculum/03-production/01-system-design/problems/url-shortener.md) | [url_shortener.py](url_shortener.py) |
| [API quota: which request spends the last token?](../../curriculum/03-production/01-system-design/problems/api-quota.md) | [api_quota.py](api_quota.py) |
| [Checkout: paid twice, ordered once?](../../curriculum/03-production/01-system-design/problems/checkout-payment.md) | [checkout_payment.py](checkout_payment.py) |
