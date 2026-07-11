"""
AutoGen용 설정 모듈.
- OPENAI_API_KEY 로딩
- OpenAIChatCompletionClient 생성
"""

import os
from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient

# .env 로드
load_dotenv()


def get_openai_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 .env 또는 환경변수에 설정되어 있지 않습니다.")
    return api_key


def create_model_client(model: str = "gpt-4o-mini") -> OpenAIChatCompletionClient:

    api_key = get_openai_api_key()
    client = OpenAIChatCompletionClient(
        model=model,
        api_key=api_key,
    )
    return client