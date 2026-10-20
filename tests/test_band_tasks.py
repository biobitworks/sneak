import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.band_client import BandClient


class BandTasksTests(unittest.TestCase):
    def test_list_tasks_empty_board(self):
        client = BandClient(api_key="test-key")
        with mock.patch.object(
            client,
            "_request",
            return_value=(200, {"data": []}),
        ):
            r = client.list_tasks("room-1")
        self.assertTrue(r["ok"])
        self.assertEqual(r["observed_outcome"], "EMPTY_BOARD")
        self.assertEqual(r["active_count"], 0)

    def test_create_task_subject_detail(self):
        client = BandClient(api_key="test-key")
        with mock.patch.object(
            client,
            "_request",
            return_value=(
                201,
                {
                    "data": {
                        "id": "t1",
                        "number": 1,
                        "subject": "do thing",
                        "detail": "more",
                        "overall_status": "pending",
                        "state": "active",
                        "chat_room_id": "room-1",
                        "created_by": {"handle": "biobitworks"},
                        "assignments": [],
                    }
                },
            ),
        ) as req:
            r = client.create_task("do thing", detail="more", room_id="room-1")
        self.assertTrue(r["ok"])
        self.assertEqual(r["task"]["number"], 1)
        args = req.call_args
        self.assertEqual(args[0][0], "POST")
        self.assertIn("/chats/room-1/tasks", args[0][1])
        self.assertEqual(args[0][2]["subject"], "do thing")
        self.assertEqual(args[0][2]["detail"], "more")

    def test_board_404_human_api(self):
        client = BandClient(api_key="test-key")
        with mock.patch.object(client, "_request", return_value=(404, {"errors": {"detail": "Not Found"}})):
            r = client.get_board("room-1")
        self.assertEqual(r["observed_outcome"], "NOT_EXPOSED_ON_HUMAN_API")


if __name__ == "__main__":
    unittest.main()
