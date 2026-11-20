from unittest.mock import MagicMock, patch

from codefox.api.llamacpp import LlamaCpp


def _provider(config: dict | None = None) -> LlamaCpp:
    with patch("codefox.api.base_api.Helper.read_yml") as read_yml:
        read_yml.return_value = config or {
            "model": {"name": "local-model"},
            "review": {"diff_only": True},
        }
        with patch("codefox.api.llamacpp.OpenAI"):
            return LlamaCpp()


def test_uses_llama_server_default_url_and_default_api_key() -> None:
    with patch.dict("os.environ", {}, clear=True):
        with patch("codefox.api.base_api.Helper.read_yml") as read_yml:
            read_yml.return_value = {
                "model": {"name": "local-model"},
                "review": {},
            }
            with patch("codefox.api.llamacpp.OpenAI") as openai:
                LlamaCpp()

    assert openai.call_args.kwargs["base_url"] == "http://localhost:8080/v1"
    assert openai.call_args.kwargs["api_key"] == "llama.cpp"


def test_connection_and_model_listing_use_openai_compatible_client() -> None:
    provider = _provider()
    provider.client.models.list.return_value = [
        MagicMock(id="local-model"),
        MagicMock(id="another-model"),
    ]

    assert provider.check_connection() == (True, None)
    assert provider.check_model("local-model") is True
    assert provider.get_tag_models() == ["local-model", "another-model"]


def test_custom_base_url_is_used() -> None:
    with patch("codefox.api.base_api.Helper.read_yml") as read_yml:
        read_yml.return_value = {
            "model": {"name": "local-model", "base_url": "http://host:9000/v1"},
            "review": {},
        }
        with patch("codefox.api.llamacpp.OpenAI") as openai:
            LlamaCpp()

    assert openai.call_args.kwargs["base_url"] == "http://host:9000/v1"
