import hashlib,json,pathlib,unittest
from scripts import build_judge_tokens
from scripts import build_evidence_heatmap as custody
from scripts import flexprice_roi_trial as roi

ROOT=pathlib.Path(__file__).resolve().parents[1]
class JudgeTokensTests(unittest.TestCase):
 def test_questions_answers_are_real_bound_but_unmetered(self):
  d=build_judge_tokens.build()
  self.assertEqual(len(d["observed_question_answer"]),2)
  a,b=d["observed_question_answer"]
  self.assertEqual(a["result"],"ACKNOWLEDGMENT_CAPTURED")
  self.assertIsNone(b["answer"])
  self.assertEqual(b["result"],"AWAITING_EVIDENCE_BOUND_HUMAN_ANSWER")
  for row in d["observed_question_answer"]:
   self.assertEqual(row["question_source"]["token_status"],"NOT_MEASURED")
   self.assertIsNone(row["question_source"]["model_id"])
   self.assertIsNone(row["question_source"]["prompt_tokens"])
   if row["answer_source"]:
    self.assertEqual(row["answer_source"]["token_status"],"NOT_MEASURED")
    self.assertIsNone(row["answer_source"]["completion_tokens"])
  self.assertEqual(d["band_planner_live"],"NOT_VERIFIED")
  self.assertEqual(d["teammate_score"],"PENDING_HUMAN_REVIEW")
 def test_synthetic_roi_math_is_independently_computed(self):
  d=build_judge_tokens.build()
  self.assertEqual(d["simulated"]["classification"],"SIMULATED_NOT_OBSERVED")
  self.assertEqual(d["simulated"]["tokens_baseline"],8000)
  self.assertEqual(d["simulated"]["tokens_sneak"],5000)
  self.assertEqual(d["simulated"]["token_reduction_fraction"],"0.375000")
  self.assertEqual(len(d["simulated"]["rows"]),6)
  for row in d["simulated"]["rows"]:
   self.assertEqual(row["prompt_tokens"]+row["answer_tokens"],row["total_tokens"])
   self.assertEqual(row["classification"],"SIMULATED_NOT_OBSERVED")
 def test_sensitive_source_chat_does_not_export(self):
  r=ROOT/"deploy/vercel-preview/data/token-journeys.json"
  payload=r.read_text()
  for marker in ["@[[","SNEAK-30b1573686bc","COGNEE_API_KEY","BAND_USER_API_KEY"]:
   self.assertNotIn(marker,payload)
  import re
  self.assertIsNone(re.search(r"sk-[a-zA-Z0-9]{18,}",payload))
 def test_merkle_export_independent_local_byte_replay(self):
  c=json.loads((ROOT/"deploy/vercel-preview/data/export-custody.json").read_text())
  self.assertTrue(custody.verify_custody(c))
  names={x["path"] for x in c["files"]}
  self.assertIn("data/token-journeys.json",names)
  self.assertIn("data/roi-demo.json",names)
  self.assertIn("tokens.html",names)
  self.assertEqual(len(names),len(c["files"]))
if __name__=="__main__":unittest.main()
