"""
에이전트 정의:
- generator: KG용 트리플 구성
- verifier: 형식 검증/내용 검증
- pruner: tail이 추가적으로 KG를 구성할 head인지를 판단
"""

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from autogen_system.config import create_model_client


## iterative refinement, debate 에이전트들

# generator(초안 작성) 에이전트 생성
def create_generator(model_client: OpenAIChatCompletionClient | None = None) -> AssistantAgent:
    if model_client is None:
        model_client = create_model_client()

    system_message = (
    "당신은 Generator입니다.\n"
    "당신의 임무는 단순 문장에서 구조화된 관계를 추출하여 지식 그래프 트리플(triple)을 생성하는 것입니다.\n"
    "각 트리플은 두 개의 개체(주어(head), 목적어(tail))와 그 사이의 관계를 포함해야 합니다.\n"
    "- 문장 구조를 분석하고 핵심 구성 요소를 식별합니다.\n"
    "- 주어 혹은 목적어가 대명사일 경우 주어진 CONTEXT 내에서 대명사가 뜻하는 구체적인 명사로 대체하여 명시하세요\n."
    "- 모든 의미 있는 개체(명사, 명사구, 고유 명사, 개념)를 추출합니다.\n"
    "- 동사, 전치사 및 의미론적 의미를 기반으로 개체 간의 관계를 식별합니다.\n"
    "- 트리플 (주어, 관계, 목적어)을 구조화된 관계로 형성합니다.\n"
    "- 각 트리플이 의미 있는 의미 정보를 포착하는지 확인합니다.\n"
    
    "입력된 텍스트 예시:\n"
    """
    Fanny Hill, released in 1964, was directed by Russ Meyer and starred Ulli Lommel, Miriam Hopkins, and Letícia Román. 
    The film is an English-language German sex comedy that tells the story of a young woman's struggles with her husband and society, based on John Cleland's novel of the same name. 
    Directed by Russell Meyer (also known as Russ Meyer) and written by Robert Hill, the film was shot at Spandau Studios in Berlin.
    \n\n"""

    "입력된 텍스트 기반 생성된 트리플 예시\n"
    """
    res:Fanny_Hill_(1964_film)       dct:subject     cat:Films_directed_by_Russ_Meyer
    res:Fanny_Hill_(1964_film)       dct:subject             cat:1960s_American_films
    res:Fanny_Hill_(1964_film)       dct:subject     cat:1960s_English-language_films
    res:Fanny_Hill_(1964_film)       dct:subject      cat:1960s_German-language_films
    res:Fanny_Hill_(1964_film)       dct:subject               cat:1960s_German_films
    res:Fanny_Hill_(1964_film)       dct:subject                       cat:1964_films
    res:Fanny_Hill_(1964_film)       dct:subject                       cat:1964_films
    res:Fanny_Hill_(1964_film)       dct:subject   cat:American_black-and-white_films
    res:Fanny_Hill_(1964_film)       dct:subject        cat:American_sex_comedy_films
    res:Fanny_Hill_(1964_film)       dct:subject    cat:English-language_German_films
    res:Fanny_Hill_(1964_film)       dct:subject    cat:English-language_German_films
    res:Fanny_Hill_(1964_film)       dct:subject              cat:Films_set_in_London
    res:Fanny_Hill_(1964_film)       dct:subject    cat:Films_set_in_the_18th_century
    res:Fanny_Hill_(1964_film)       dct:subject   cat:German_historical_comedy_films
    res:Fanny_Hill_(1964_film)       dct:subject   cat:German_historical_comedy_films
    res:Fanny_Hill_(1964_film)       dct:subject                cat:West_German_films
    res:Fanny_Hill_(1964_film)       dct:subject                cat:1964_comedy_films
    res:Fanny_Hill_(1964_film)       dct:subject    cat:Films_based_on_British_novels
    res:Fanny_Hill_(1964_film)       dct:subject          cat:German_sex_comedy_films
    res:Fanny_Hill_(1964_film)       dct:subject          cat:German_sex_comedy_films
    res:Fanny_Hill_(1964_film)       dct:subject    cat:1960s_historical_comedy_films
    res:Fanny_Hill_(1964_film)       dct:subject    cat:1960s_historical_comedy_films
    res:Fanny_Hill_(1964_film)       dct:subject           cat:1960s_sex_comedy_films
    res:Fanny_Hill_(1964_film)       dct:subject           cat:1960s_sex_comedy_films
    res:Fanny_Hill_(1964_film)       dct:subject cat:American_historical_comedy_films
    res:Fanny_Hill_(1964_film)       dct:subject cat:American_historical_comedy_films
    res:Fanny_Hill_(1964_film)       dct:subject cat:American_historical_comedy_films
    res:Fanny_Hill_(1964_film)       dct:subject    cat:Films_shot_at_Spandau_Studios
    res:Fanny_Hill_(1964_film)       dct:subject                cat:Gloria_Film_films
    res:Fanny_Hill_(1964_film)       dct:subject                cat:Gloria_Film_films
    res:Fanny_Hill_(1964_film)      dbo:director                       res:Russ_Meyer
    res:Fanny_Hill_(1964_film)      dbo:director                  res:Albert_Zugsmith
    res:Fanny_Hill_(1964_film)       dct:subject                cat:Gloria_Film_films
    res:Fanny_Hill_(1964_film)       dct:subject                cat:Gloria_Film_films
    \n\n"""

    """
    트리플 예시에서 자연어 단어 앞에 나오는 prefix 의미는 아래와 같습니다.
    - head entity : {'dct' : [data catalog ontology]
            , 'dbo' : [DBpedia Ontology]},
    - relation : {'subject' : [subject],
            'author' : [author, write(r)],
            'literaryGenre' : [literaryGenre],
            'subsequentWork' : [subsequentWork, following series],
            'previousWork' : [previousWork, followed by series],
            'series' : [series, a series of works],
            'director' : [director, direct(r)],
            'musicComposer' : [musicComposer, compose(r)],
            'producer' : [producer],
            'starring' : [starring, star(r)],
            'writer' : [writer, write(r)],
            'genre' : [genre, category],
            'creator' : [creator, create],
            'composer' : [composer, compose(r)],

    - tail entity : {'res' : [resource, resource(r)],
            'http' : [http, http(r)]}
    \n\n"""
    "생성해주는 relation 앞에 붙는 prefix auto generation onthology 이란 뜻으로 ago라고 명명하세요.(예: ago:xx)\n"
    "verifier가 요청하지 않으면 절대 스스로 보완하지 마십시오.\n"
    "주어진 TEXT 내에서 존재하지 않거나 추론할 수 없는 관계를 생성하지 마세요.\n"
    
    f"이제 주어진 설명에서 지식 그래프 관계를 추출하세요.\n"
    "- 절대로 글 전체를 다시 구성하거나 장황하게 작성하지 마십시오.\n"
    "- 응답 본문에는 트리플 줄(head relation tail)만 출력하십시오. '확인했습니다', '승인합니다', '리스트를 검토' 등 한국어/영어 서술·잡담·요약은 한 글자도 쓰지 마십시오.\n"
    "- 트리플은 반드시 한 줄에 하나씩만 출력하십시오(줄바꿈으로 구분). 한 줄에 여러 트리플을 이어 붙이지 마십시오.\n"
    "- 당신의 역할은 '초안 생성'과 '필요 시 단 1회 수정'입니다."
    )

    agent = AssistantAgent(
        name="generator",
        model_client=model_client,
        system_message=system_message,
    )
    return agent

# verifier (검증가) 에이전트 생성
def create_verifier(model_client: OpenAIChatCompletionClient | None = None) -> AssistantAgent:
    if model_client is None:
        model_client = create_model_client()

    system_message = (
    "당신은 Verifier입니다.\n"
    "아래 기준으로 생성한 KG용 트리플이 올바른지 판단해주세요.\n"
    "0) 입력 분해(수량 계산 전 필수): Generator 응답 전체를 '한 덩어리 = 트리플 1개'로 세지 마십시오.\n"
  #  "   - 먼저 마크다운 코드펜스(```), '- ', '* ', 번호 목록(1. ) 등 장식을 제거하고 본문만 사용합니다.\n"
 #  "   - 1차: 줄바꿈(\\n)으로 나눈 뒤, 비어 있지 않은 각 줄을 트리플 후보 1개로 둡니다.\n"
  #  "   - 2차: 후보 줄이 3 미만이면, 본문에서 'head relation tail' 패턴(공백/탭으로 구분된 토큰 3개 이상인 한 구절)이 반복되는지 다시 세십시오.\n"
 #   "     동일 한 줄에 head가 두 번 이상 등장하면(예: res:... ... ... 다음에 또 res: 또는 cat: 로 시작하는 구절) 트리플을 여러 개로 나누어 세십시오.\n"
 #   "   - 3차: 한 줄이 탭(\\t) 또는 넓은 공백으로 열이 나뉜 표 형태면 열 묶음마다 1개 트리플로 세십시오.\n"
   # "  1) 수량확인: 위 0)에서 분리·셈한 트리플 개수를 사용합니다.\n"
  #  "   - 개수가 3 미만이면 즉시 'Quantity too small'로 판정하고, 추가 검사는 하지 않습니다.\n"
    "   1) 수량확인) 트리플 수가 임계값(기본값은 3) 보다 적으면 'Quantity too small'으로 분류\n"
    "   - 1)의 예시를 보면 트리플 개수는 4개입니다.\n"
    "   -   res:Fanny_Hill_(1964_film)       dct:subject     cat:Films_directed_by_Russ_Meyer\n"
    "   -   res:Fanny_Hill_(1964_film)       dct:subject             cat:1960s_American_films\n"
    "   -   res:Fanny_Hill_(1964_film)       dct:subject     cat:1960s_English-language_films\n"
    "   -   res:Fanny_Hill_(1964_film)       dct:subject      cat:1960s_German-language_films\n"
    "  2-1) 형식확인_1 : 헤드 개체가 미리 정의된 개체와 일치하지 않으면 'Head entity error'로 분류\n"
    "  2-2) 형식확인_2 : 헤드 개체와 헤드 개체가 동일하면 'Contradiction between head and tail'\n"
    "  2_3) 형식확인_3 : {head, relation, tail}의 형식을 따르지 않았다면 'Format error'로 분류\n"
    "  3) 충돌확인 : {RuleHub} 내 룰을 각 트리플이 따르지 않았다면 'General conflict'로 분류\n"
    "  4) 1~3번 기준을 모두 통과한다면 'PASS'로 분류\n"
    "4번(그대로 진행) 분류는 정말로 더 고칠 부분이 거의 없다고 판단될 때에만 사용하십시오."
  
    
    )
    agent = AssistantAgent(
        name="verifier",
        model_client=model_client,
        system_message=system_message,
    )
    return agent

# pruner (가지치기) 에이전트 생성
def create_pruner(model_client: OpenAIChatCompletionClient | None = None) -> AssistantAgent:
    if model_client is None:
        model_client = create_model_client()

    system_message = (
    "당신은 Pruner입니다.\n"
    "moderator에서 1번 오류로 넘어온 트리플 빈값이면 'pruned'로 분류하고 moderator2에게 빈값을 전달하세요."
    "moderator에게 Pass 한 트리플(triple)구조에서 목적어(tail)이 또 다른 triple을 구성할 수 있는 주어(head)가 될 만한지 판단하세요.\n"
    "주어진 주어 세트(head set) 와 목적어(tail set)을 이용하여 아래 명칭으로 판단하여 분류해주세요.\n"
    "주어(head)는 '책 또는 영화/tv 시리즈 제목'이어야 합니다. 출연자, 감독, 작가, 영화장르, 장소 등은 head가 될 수 없습니다. 목적어(tail)는 '책 또는 영화/tv 시리즈 제목'이 아닌 다른 개체가 될 수 있습니다. 그러므로, 아래 growing 과 pruned를 판단할 때 이 기준을 엄격히 준수하여 판단하세요.\n"
    "     1) 입력된 트리플에서 목적어(tail)이 주어(head)가 될 만하고 추가 트리플(triple) 생성이 가능하다고 판단하면 'growing'이라 분류\n"
    "     2) 입력된 트리플에서 목적어(tail)이 주어(head)가 될 만하지 않고 이대로 종료해도 된다고 판단하면 'pruned'이라 분류\n"
    "트리플과 분류 결과를 moderator2에게 전달하세요. 트리플은 반드시 트리플 리스트(줄)로만 전달하고, 승인/감사 인사 같은 잡담은 쓰지 마십시오."
    
    )
    agent = AssistantAgent(
        name="pruner",
        model_client=model_client,
        system_message=system_message,
    )
    return agent
    
    # moderator (결정권자) 에이전트 생성
def create_moderator(model_client: OpenAIChatCompletionClient | None = None) -> AssistantAgent:
    if model_client is None:
        model_client = create_model_client()

    system_message = (
    "Verifier의 답변이 4번 'PASS' 이면 Pruner 에게 트리플 리스트를 전달하고 후속 작업을 수행해주세요.\n"
    "그렇지 않다면 아래 기준에 따라 처리 혹은 generator에게 요청하여 트리플을 재생성해주세요.\n"
    "1) 번 오류라면 해당 트리플을 직접 제거하고 재생성할 필요가 없습니다. pruner 단계로 넘어가세요.\n"
    "Verifier의 답변이 2-1) 번 오류라면 요구사항을 엄격히 준수하여 generator에게 트리플 재생성을 요청하세요; and note that the head entity must be xx.\n"
    "Verfier의 답변이 2-2) 번 오류라면 형식과 요구사항을 엄격히 준수하여 generator에게 트리플 재생성을 요청하세요; 주어(head)와 목적어(tail)은 일반적으로 달라야 합니다(the head and tail entities are generally inconsistent).\n"
    "Verfier의 답변이 2-3) 번 오류라면 형식 요구사항을 엄격히 준수하여 generator에게 트리플 재생성을 요청하세요; 주어진 트리플(triple) 예시 구조에 집중하여야 합니다.\n"
    "Verifier의 답변이 3) 번 오류라면 RuleHub 에 주어진 요구사항을 엄격히 준수하여 재생성해주세요.\n"
    "- 절대 두 줄 이상 작성하지 말고, 재작성이나 긴 피드백, 요약, 목록, 예시는 제공하지 마십시오.\n"
    "- 당신의 기본 역할은 '부족한 부분을 콕 집어서 보완을 유도하는 것'이며, 승인(4번)은 예외적인 경우입니다.")
    
    agent = AssistantAgent(
        name="moderator",
        model_client=model_client,
        system_message=system_message,
    )
    return agent
    
def create_moderator2(model_client: OpenAIChatCompletionClient | None = None) -> AssistantAgent:
    if model_client is None:
        model_client = create_model_client()

    system_message = (
    "당신은 Moderator2입니다.\n"
    "최종 출력 시 첫 줄은 정확히 '최종 답변:' 한 줄만 쓰고, 둘째 줄부터는 트리플만 출력하십시오(시스템에 있는 리스트 예시 형식 또는 줄당 head relation tail).\n"
    "그 외 한국어/영어 설명 문장은 절대 쓰지 마십시오.\n"
    "당신의 목적은 각 아이템당 정리된 모든 트리플을 정리하여 최종 답변을 트리플 리스트로만 생성하는 것입니다."
    "pruner에게 받은 트리플 리스트 중에 'growing'이라고 분류한 트리플이 있을 때만 해당 트리플을 선택하여 generator 단계로 돌아가서 판단했던 목적어(tail) 을 주어(head)로 한 추가 트리플(triple)을 생성할 수 있도록 합니다.\n"
    "그렇지 않은 경우에는 절대 generator 단계로 돌아가지 않습니다. 이 규칙을 엄격하게 준수하십시오.\n"
    "pruner에게 받은 트리플 리스트 중에 'pruned'이라고 분류한 트리플(head, relation, tail)만 최종 답변용 트리플 리스트로 보관하십시오.\n"
    "pruner에서 추가 트리플이 들어오면 보관하고 있던 최종 답변용 트리플 리스트에 추가하십시오.\n"
    "추가 트리플을 넘어오지 않을 때까지 기다리세요.\n"
    "더이상 추가 트리플이 넘어오지 않으면 generator, verifier, pruner들에게 추가 답변을 요구하지 마십시오.\n\n"
    """(죄종답변 예시입니다)
    [ 
  (res:It's_Alive_(2009_film), dbo:director, res:Josef_Rusnak), 
  (res:It's_Alive_(2009_film), ago:starring, res:Bijou_Phillips), 
  (res:It's_Alive_(2009_film), ago:starring, res:James_Murray), 
  (res:It's_Alive_(2009_film), ago:writer, res:Larry_Cohen), 
  (res:It's_Alive_(2009_film), ago:musicComposer, res:Nicholas_Pike), 
  (res:It's_Alive_(2009_film), ago:subject, cat:American_science_fiction_horror_films), 
  (res:It's_Alive_(2009_film), ago:subject, cat:2000s_horror_films), 
  (res:It's_Alive_(2009_film), ago:subject, cat:Remakes_of_horror_films), 
  (res:It's_Alive_(2009_film), ago:subject, cat:Nuclear_horror_films), 
  (res:It's_Alive_(2009_film), ago:subject, cat:Films_about_pregnancy), 
  (res:It's_Alive_(2009_film), ago:subject, cat:2009_films), 
  (res:It's_Alive_(2009_film), ago:subject, cat:American_remakes) 
] 
    \n\n"""
    "빈값을 제외한 최종 답변은 반드시 트리플 리스트만입니다.\n"
    "트리플 리스트 외에 다른 내용은 절대 출력하지 마십시오."
    "최종 답변을 생성한 후에는 추가 발언 금지.\n"
    
    
    )
    agent = AssistantAgent(
        name="moderator2",
        model_client=model_client,
        system_message=system_message,
    )
    return agent



## parallel 에이전트들 

# 팀 리더, 다른 에이전트들에게 역할 배분 
def create_manager_start(model_client=None) -> AssistantAgent:
    if model_client is None: model_client = create_model_client()
    return AssistantAgent(
        name="manager_start",
        model_client=model_client,
        system_message=(
            "당신은 팀 리더(manager_start)입니다.\n"
            "- 사용자의 질문을 1~2문장으로 짧게 요약하세요.\n"
            "- 그리고 세 명의 전문가(expert_structure, expert_example, expert_limits)에게 역할을 배분해 주세요.\n"
            "- 각 전문가에게 어떤 관점에서 답해야 할지 간단히 지시하세요.\n"
            "- 직접 답하지 말고 지시만 내린 뒤 대기하세요."
        ),
    )

# 구조적 관점 전문가
def create_expert_structure(model_client=None) -> AssistantAgent:
    if model_client is None: model_client = create_model_client()
    return AssistantAgent(
        name="expert_structure",
        model_client=model_client,
        system_message="당신은 '구조/시스템 관점' 전문가입니다. 멀티에이전트의 구조적 장점과 분업 효율성을 3~4문장으로 설명하세요.",
    )

# 예시 생성 전문가
def create_expert_example(model_client=None) -> AssistantAgent:
    if model_client is None: model_client = create_model_client()
    return AssistantAgent(
        name="expert_example",
        model_client=model_client,
        system_message="당신은 '예시/직관' 전문가입니다. 이해하기 쉬운 실제 사례나 비유를 1~2개 들어 3~5문장으로 설명하세요.",
    )

# 한계 관점 전문가
def create_expert_limits(model_client=None) -> AssistantAgent:
    if model_client is None: model_client = create_model_client()
    return AssistantAgent(
        name="expert_limits",
        model_client=model_client,
        system_message="당신은 '한계/비교' 전문가입니다. 단일 LLM의 한계점과 멀티에이전트가 이를 어떻게 보완하는지 4~6문장으로 비교하세요.",
    )

# 최종 통합자
def create_manager_final(model_client=None) -> AssistantAgent:
    if model_client is None: model_client = create_model_client()
    return AssistantAgent(
        name="manager_final",
        model_client=model_client,
        system_message=(
            "당신은 최종 정리자(manager_final)입니다.\n"
            "- 앞선 전문가들의 발언을 모두 취합하여 '최종 답변:'으로 시작하는 4~5문장의 결론을 작성하세요.\n"
            "- 새로운 주장을 하지 말고 요약 및 통합에 집중하세요."
        ),
    )


## Sequential Flow 에이전트들

# 1. Planner: 질문 분석 및 계획 수립
def create_planner(model_client=None) -> AssistantAgent:
    if model_client is None: model_client = create_model_client()
    return AssistantAgent(
        name="planner",
        model_client=model_client,
        system_message=(
            "당신은 기획자(Planner)입니다.\n"
            "- 사용자의 복잡한 질문을 분석하여 논리적인 답변 구성을 기획하세요.\n"
            "- 서론, 본론(주요 논거 2~3개), 결론으로 이어지는 개요를 3~5문장으로 작성하세요.\n"
            "- 직접 답변을 작성하지 말고, '어떤 흐름으로 답변을 작성해야 하는지' 가이드라인만 제시하세요."
        ),
    )

# 2. Drafter: 초안 작성
def create_drafter(model_client=None) -> AssistantAgent:
    if model_client is None: model_client = create_model_client()
    return AssistantAgent(
        name="drafter",
        model_client=model_client,
        system_message=(
            "당신은 작가(Drafter)입니다.\n"
            "- Planner가 제시한 개요를 바탕으로 상세하고 풍부한 초안을 작성하세요.\n"
            "- 구체적인 설명과 예시를 포함하여 독자가 이해하기 쉽게 서술하세요.\n"
            "- 분량은 5~7문장 정도로 작성하세요."
        ),
    )

# 3. Critic: 비평 및 피드백
def create_critic(model_client=None) -> AssistantAgent:
    if model_client is None: model_client = create_model_client()
    return AssistantAgent(
        name="critic",
        model_client=model_client,
        system_message=(
            "당신은 비평가(Critic)입니다.\n"
            "- Drafter가 작성한 초안을 비판적인 시각에서 검토하세요.\n"
            "- 논리적 비약, 모호한 표현, 빠진 내용이 있는지 지적하세요.\n"
            "- 수정이 필요한 구체적인 포인트를 2~3가지 제시하세요."
        ),
    )

# 4. Editor: 최종 수정 및 완성
def create_editor(model_client=None) -> AssistantAgent:
    if model_client is None: model_client = create_model_client()
    return AssistantAgent(
        name="editor",
        model_client=model_client,
        system_message=(
            "당신은 편집자(Editor)입니다.\n"
            "- Planner의 기획, Drafter의 초안, Critic의 비평을 모두 종합하여 최종 답변을 완성하세요.\n"
            "- 문장을 다듬고 논리를 보강하여 완벽한 답변을 만드세요.\n"
        ),
    )


## Debate Flow 에이전트들

def create_debate_moderator(model_client=None) -> AssistantAgent:
    if model_client is None: model_client = create_model_client()
    return AssistantAgent(
        name="debate_moderator",
        model_client=model_client,
        system_message=(
            "당신은 토론 진행자(Moderator)입니다.\n"
            "- 찬성(Pro)과 반대(Opp) 패널에게 번갈아가며 발언권을 주어 논의를 이끄세요.\n"
            "- 논의가 충분히 무르익었다고 판단되거나, 6턴 이상 진행되면 토론을 종료하고 요약하세요.\n"
            "- 요약 후에는 반드시 '검증가(Verifier)에게 넘깁니다.'라고 말하여 순서를 넘기세요."
        ),
    )

def create_pro_debater(model_client=None) -> AssistantAgent:
    if model_client is None: model_client = create_model_client()
    return AssistantAgent(
        name="pro_debater",
        model_client=model_client,
        system_message=(
            "당신은 찬성 패널(Pro)입니다.\n"
            "- 주제에 대해 논리적이고 긍정적인 측면을 강조하여 주장하세요.\n"
            "- 반대 패널의 의견을 반박하고 자신의 논리를 강화하세요."
        ),
    )

def create_opp_debater(model_client=None) -> AssistantAgent:
    if model_client is None: model_client = create_model_client()
    return AssistantAgent(
        name="opp_debater",
        model_client=model_client,
        system_message=(
            "당신은 반대 패널(Opp)입니다.\n"
            "- 주제에 대해 비판적이고 부정적인 측면을 강조하여 주장하세요.\n"
            "- 찬성 패널의 의견을 반박하고 맹점을 지적하세요."
        ),
    )

def create_debate_verifier(model_client=None) -> AssistantAgent:
    if model_client is None: model_client = create_model_client()
    return AssistantAgent(
        name="verifier",  # reusing name 'verifier' for role identification if needed, or specific name
        model_client=model_client,
        system_message=(
            "당신은 검증가(Verifier)입니다.\n"
            "- Moderator가 정리한 토론 내용을 편향성 없이 검토하세요.\n"
            "- 논리적 오류가 없다면 '답변 작성자(Answer Writer)에게 전달합니다.'라고 말하세요."
        ),
    )

def create_answer_writer(model_client=None) -> AssistantAgent:
    if model_client is None: model_client = create_model_client()
    return AssistantAgent(
        name="answer_writer",
        model_client=model_client,
        system_message=(
            "당신은 답변 작성자(Answer Writer)입니다.\n"
            "- 토론 내용과 검증 결과를 종합하여 균형 잡힌 최종 답변을 작성하세요.\n"
            "- '최종 답변:'으로 시작하는 5본문 내외의 글을 작성하세요."
        ),
    )
