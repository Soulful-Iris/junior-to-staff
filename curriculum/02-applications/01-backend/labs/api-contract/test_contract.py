import unittest
from boundary import application, edge_request, envelope, proxy_passthrough


class ContractTests(unittest.TestCase):
    def test_response_model_is_not_a_runtime_body_validator(self):
        invalid = envelope(200, {"total_cents": "200"})
        self.assertEqual(proxy_passthrough(invalid), (200, {"total_cents": "200"}))
        fixed = application('{"quantity":2}', "application/json", {"limit": "20"}, lambda _: {"total_cents": "200"})
        self.assertEqual(proxy_passthrough(fixed), (502, {"error": "invalid_provider_response"}))

    def test_valid_contract_and_invalid_200_variants(self):
        self.assertEqual(proxy_passthrough(application('{"quantity":2}', "application/json", {"limit": "20"}, lambda q: {"total_cents": q*100})), (200, {"total_cents": 200}))
        for invalid in ({}, {"total_cents": True}, {"total_cents": -1}, {"total_cents": 2, "internal_secret": "x"}, None):
            with self.subTest(invalid=invalid):
                self.assertEqual(application('{"quantity":2}', "application/json", {"limit": "20"}, lambda _, value=invalid: value)["statusCode"], 502)

    def test_basic_parameter_presence_is_not_format_validation(self):
        self.assertIsNone(edge_request('{"quantity":2}', "application/json", {"limit": "banana"}))
        result = application('{"quantity":2}', "application/json", {"limit": "banana"}, lambda _: self.fail("provider must not run"))
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(edge_request('{"quantity":2}', "application/json", {}), 400)

    def test_unmatched_content_type_and_default_model_are_separate_choices(self):
        self.assertIsNone(edge_request('{"quantity":"bad"}', "text/plain", {"limit": "20"}))
        self.assertEqual(edge_request('{"quantity":"bad"}', "text/plain", {"limit": "20"}, default_model=True), 400)
        self.assertEqual(application('{"quantity":2}', "text/plain", {"limit": "20"}, lambda _: self.fail("no provider call"))["statusCode"], 415)

    def test_invalid_requests_and_proxy_envelope(self):
        for body in ('not-json', '{"quantity":0}', '{"quantity":true}', '{}'):
            self.assertEqual(edge_request(body, "application/json", {"limit": "20"}), 400)
            self.assertEqual(application(body, "application/json", {"limit": "20"}, lambda _: self.fail("no provider call"))["statusCode"], 400)
        self.assertEqual(proxy_passthrough({"statusCode": 200, "body": {"total_cents": 200}})[0], 502)


if __name__ == "__main__":
    unittest.main()
