"""
AutoGen 반복 정제(Iterative Refinement) 워크플로우:
Debater, Verifier, Moderator를 RoundRobinGroupChat으로 묶어서
질문 하나에 대해 협력적으로 답변을 만들어내는 흐름을 정의한다.
"""

import re

from autogen_agentchat.base import TaskResult
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import TextMessage

from autogen_system.agents import create_generator, create_verifier, create_pruner, create_moderator, create_moderator2
from autogen_system.config import create_model_client


#MAIN_QUESTION = f"""
#다음 설명을 보고 한 아이템에 대한 여러 개의 트리플 형태로 구현해주세요
#{sentence}
#"""
def build_main_question(question: str) -> str:
  return f"""
다음 설명을 보고 한 아이템에 대한 여러 개의 트리플 형태로 구현해주세요
{question}
""".strip()


_PREFIX = r"(?:res|dct|dbo|ago|cat|http)"
# 공백 구분 줄: head relation tail (tail에 공백·따옴표 허용)
_WS_TRIPLE = re.compile(
    rf"^(?P<h>{_PREFIX}:\S+)\s+(?P<r>{_PREFIX}:\S+)\s+(?P<t>.+)$",
    re.IGNORECASE,
)
# (head, relation, tail) 한 줄 — tail에 쉼표가 있어도 마지막 그룹이 흡수
_PAREN_TRIPLE = re.compile(
    r"^\(\s*(?P<h>.+?)\s*,\s*(?P<r>.+?)\s*,\s*(?P<t>.+)\s*\)\s*,?\s*$",
)


def _parse_triple_line(line: str) -> dict[str, str] | None:
    line = line.strip()
    if not line or line in ("[", "]"):
        return None
    if line.startswith(("- ", "* ")):
        line = line[2:].strip()
    if line.startswith(("결론", "#", "```")) or (line.startswith("[") and line.endswith("]")):
        return None

    m = _WS_TRIPLE.match(line)
    if m:
        return {
            "head": m.group("h").strip(),
            "relation": m.group("r").strip(),
            "tail": m.group("t").strip(),
        }
    m = _PAREN_TRIPLE.match(line)
    if m:
        h, r, t = m.group("h").strip(), m.group("r").strip(), m.group("t").strip()
        if re.match(rf"^{_PREFIX}:", h, re.I):
            return {"head": h, "relation": r, "tail": t}
    return None


def triples_from_task_result(processed: TaskResult) -> list[dict[str, str]]:
    """대화 로그에서 head/relation/tail dict 리스트로 정규화하고, (h,r,t) 기준 중복 제거."""
    out: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for msg in processed.messages:
        body = getattr(msg, "content", None)
        if not body:
            continue
        text = str(body).strip()
        for prefix in ("최종 답변:", "최종답변:"):
            if text.startswith(prefix):
                text = text[len(prefix) :].strip()
                break
        for raw in text.splitlines():
            line = raw.strip()
            parsed = _parse_triple_line(line)
            if parsed is None:
                continue
            key = (parsed["head"], parsed["relation"], parsed["tail"])
            if key in seen:
                continue
            seen.add(key)
            out.append(parsed)
    return out


async def run_iterative_refinement_workflow(question: str | None = None) -> list[dict[str, str]] | None:
    """
    Iterative Refinement 방식 기반 멀티에이전트 팀을 구성하고,
    하나의 질문에 대한 협업 대화를 수행
    """
    #if question is None:
        #question = MAIN_QUESTION.strip()
    #    question = build_main_question(question)

    # None 방어 : 빈 질문이면 그냥 종류
    if not question:
        return None

    # 실제 작업 지시문 생성
    question = build_main_question(question)

    # 하나의 model_client를 세 에이전트가 공유
    model_client = create_model_client()

    generator = create_generator(model_client)
    verifier = create_verifier(model_client)
    moderator = create_moderator(model_client)
    pruner = create_pruner(model_client)
    moderator2 = create_moderator2(model_client)


    # 종료: moderator2가 '최종 답변:'을 붙였을 때, 또는 상한(메시지 델타 누적이 크면 10도 빨리 찬다).
    termination = TextMentionTermination(text="최종 답변:") | MaxMessageTermination(max_messages=40)

    # 팀 구성: Generator -> Verifier -> Pruner -> Moderator 순환
    # RoundRobinGroupChat 클래스 자체는 그대로 사용하되, 개념적으로 Iterative Refinement를 수행
    team = RoundRobinGroupChat(
        participants=[generator, verifier, moderator, pruner, moderator2], # 멤버 정의
        termination_condition=termination, # 종료 조건
    )

    # TextMessage를 사용해 질문 전달
    task = TextMessage(
        content=(
            "다음 질문에 대해 팀이 협력하여 답변을 만들어주세요.\n\n"
            f"{question}"
        ),
        source="user",
    )
    
    # 스트림은 한 번만 소비: Console이 터미널 포맷을 담당하고, 마지막 TaskResult를 반환한다.
    stream = team.run_stream(task=task)
    processed = await Console(stream)
    await model_client.close()

    if not isinstance(processed, TaskResult):
        return None
    return triples_from_task_result(processed)