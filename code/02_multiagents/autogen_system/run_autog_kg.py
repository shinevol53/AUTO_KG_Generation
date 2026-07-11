import asyncio
import pandas as pd
import json
from pathlib import Path
from workflow_iterative_refinement import run_iterative_refinement_workflow


INPUT_CSV = Path("/Users/baebichna/git_repo/Amazon-KG-v2.0-dataset/triples_to_summary_movies_instruct.csv")
OUTPUT_CSV = Path("/Users/baebichna/git_repo/multiagents/results_from_multiagents.csv")
ITEM_COL = "title"  # 영화/리소스 아이템 (예: res:It's_Alive_(2009_film))
TEXT_COL = "summary"
LIMIT = None  # 전체 돌리려면 None
# N행 처리할 때마다 CSV 덮어쓰기(체크포인트). None이면 종료 시 한 번만 저장.
SAVE_EVERY_N = 500  # 300 단위로 쓰려면 300으로 변경


def _write_results_csv(rows: list, path: Path) -> None:
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8")


async def main():
  df = pd.read_csv(INPUT_CSV)
  for col in (ITEM_COL, TEXT_COL):
      if col not in df.columns:
          raise ValueError(f"컬럼 '{col}' 없음. 사용 가능 컬럼: {list(df.columns)}")
  rows = []
  sub = df[[ITEM_COL, TEXT_COL]].dropna(subset=[TEXT_COL]).astype(str)
  if LIMIT is not None:
      sub = sub.head(LIMIT)
  for idx, row in sub.iterrows():
      item = row[ITEM_COL]
      sentence = row[TEXT_COL]
      print(f"[{idx}] start")
      try:
          triples = await run_iterative_refinement_workflow(sentence)
          rows.append({
              "idx": idx,
              "item": item,
              "sentence": sentence,
              "result": json.dumps(triples, ensure_ascii=False) if triples is not None else None,
              "error": None,
          })
      except Exception as e:
          rows.append({
              "idx": idx,
              "item": item,
              "sentence": sentence,
              "result": None,
              "error": str(e),
          })
          print(f"[{idx}] error: {e}")
      if SAVE_EVERY_N and len(rows) % SAVE_EVERY_N == 0:
          _write_results_csv(rows, OUTPUT_CSV)
          print(f"checkpoint: {len(rows)} rows → {OUTPUT_CSV}")
  _write_results_csv(rows, OUTPUT_CSV)
  print(f"saved: {OUTPUT_CSV} ({len(rows)} rows)")


if __name__ == "__main__":
  asyncio.run(main())