# Automated Knowledge Graph Generation for Cross-Domain Recommendation Using Multi-Agent Systems


------------------------------------------------------------------------------------------------
## Overview
이 프로젝트는 멀티 에이전트 기반 LLM 협업을 활용해 cross-domain recommendation을 위한 knowledge graph를 자동 구축하는 방법론을 제안합니다. 생성된 KG는 source domain의 구조적 의미를 보존한 채 embedding space로 전이되며, target domain 추천 모델의 성능 향상에 활용됩니다.

## Motivation
기존 CDR 방법은 사용자/아이템 상호작용 전이에 집중하는 경우가 많아, 도메인 간 관계 의미와 스키마 차이를 충분히 반영하지 못합니다. 특히 heterogeneous relation distribution, naming convention 차이, schema granularity 문제는 직접적인 전이를 어렵게 만듭니다.

## Proposed Method
제안 방법론은 두 단계로 구성됩니다.
1. Multi-agent based KG construction
2. KG embedding transfer for target recommendation

## Architecture
![프로젝트 구조도](./img/AutomatedKG_Flow_3.drawio.png)

## Multi-Agent KG Construction
- Generator: RDF triple 후보 생성
- Verifier: triple의 구조 및 의미 검증
- Validation Moderator: 검증 결과 조정
- Pruner: 저품질/중복 triple 제거
- Expansion Moderator: 그래프 확장 여부 결정

![멀티에이전트 오케스트레이션](./img/멀티에이전트오케스트레이션.PNG)

## Embedding Transfer
구축된 source KG는 TransE로 임베딩되며, 이후 KGBridge를 통해 target sequential recommendation에 반영됩니다.

## Experimental Setting

- Dataset: Amazon Books, Movie/TV
- Source KG construction: Amazon metadata + LLM-based multi-agent pipeline
- Embedding model: TransE
- Downstream recommender: KGBridge
- Metrics: Recall, NDCG, MRR

실험에서는 위 설정하에서 정형(구조화) 트리플과 비정형(비정형 데이터 기반) 트리플의 구성 비율을 여러 수준으로 바꾸어, 각 구성에 대해 동일한 추천 모델의 성능을 비교하였다.


## Key Findings
실험 결과, 전이 비율이 무조건 높을수록 좋은 것은 아니며, 중간 수준의 transfer setting이 더 안정적인 성능을 보였습니다. 이는 cross-domain 구조 전이에서 정보량보다 관계 정합성과 의미 보존이 더 중요함을 시사합니다.

## Contributions
- Multi-agent 기반 KG 자동 구축 프레임워크 제안
- Cross-domain recommendation을 위한 KG embedding transfer 설계
- 구조적 이질성과 의미 정합성 문제를 실험적으로 분석

