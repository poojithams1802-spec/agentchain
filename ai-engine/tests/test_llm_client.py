import pytest

from llm_client import GeminiClient


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeModels:
    def __init__(self, response):
        self.response = response

    def generate_content(self, **kwargs):
        return self.response


class FakeClient:
    def __init__(self, response):
        self.models = FakeModels(response)


def create_test_client(response):
    client = object.__new__(GeminiClient)
    client.client = FakeClient(response)
    client.model = "test-model"
    return client


def test_generate_json_returns_valid_object():
    client = create_test_client(
        FakeResponse(
            '{"selected_test": "check_permissions"}'
        )
    )

    result = client.generate_json("test prompt")

    assert result == {
        "selected_test": "check_permissions"
    }


def test_generate_json_rejects_malformed_json():
    client = create_test_client(
        FakeResponse("not valid json")
    )

    with pytest.raises(ValueError, match="malformed JSON"):
        client.generate_json("test prompt")


def test_generate_json_rejects_non_object_json():
    client = create_test_client(
        FakeResponse('["item1", "item2"]')
    )

    with pytest.raises(
        ValueError,
        match="must be a JSON object"
    ):
        client.generate_json("test prompt")


def test_generate_json_rejects_empty_response():
    client = create_test_client(
        FakeResponse("")
    )

    with pytest.raises(
        ValueError,
        match="empty response"
    ):
        client.generate_json("test prompt")