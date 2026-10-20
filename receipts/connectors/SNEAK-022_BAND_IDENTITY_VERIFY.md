# SNEAK-022 BAND identity verification

- Auth: Human API as `biobitworks` (`06699f5d-d559-4bf7-a608-222d1b0fb9a1`) — **True**
- Desktop `band` CLI on this VM: **False** (needs Band Desktop/jamd)
- Target room: `7e218ad7-4d4e-4a07-a3b2-d4db8a03b4c3`
- Sneak room: `20f1ee5f-6f5b-46c5-9271-0ba536d322fd`
- Active tasks (target) before→after: **1 → 1**
- Board goal endpoint (Human API): **NOT_EXPOSED_ON_HUMAN_API**
- Tom/Jerry mention: **True**

## Agent identities

| Harness | Configured id | Live name | Match |
|---|---|---|---|
| claude | `3926218d-8342-4667-9f07-5b556b50fb7f` | Tom | **True** |
| chatgpt | `8b51f295-c2e7-4aaa-99dd-5f2335dcab49` | Jerry | **True** |

Empty Tasks UI = zero active shared tasks. Filing `POST /chats/{id}/tasks` with `{subject, detail}` populates the board.

## Agent ACKs

- `84a6c57c-ae1a-4586-8d1c-e6f30c3f558e`: ACK from Tom. Handle: @[[06699f5d-d559-4bf7-a608-222d1b0fb9a1]]/tom. I'm in room 7e218ad7-4d4e-4a07-a3b2-d4db8a03b4c3 (my workspace directory is named for it). I have no tool that reads the board or its task count, so I can't confirm "active tasks = 1" myself. I printed no secret
- `4869ca23-a80b-408f-b21b-61c215b81b88`: {"name": "band_send_message", "args": {"content": "ACK from Tom. Handle: @biobitworks/tom. I'm in room 7e218ad7-4d4e-4a07-a3b2-d4db8a03b4c3 (my workspace directory is named for it). I have no tool that reads the board or its task count, so I can't confirm \"active tasks = 1\" mys
- `abdd5ef5-f523-4042-b08a-d770c086832a`: ACK again from Jerry 🐭 — handle @[[06699f5d-d559-4bf7-a608-222d1b0fb9a1]]/jerry. I'm in this room (working dir is named for 7e218ad7-...), but I can't independently verify the task count — no board tool on my side. No secrets printed 🧀
- `a92eb19f-6483-4343-acec-c7846a4fc7a8`: {"name": "band_send_message", "args": {"content": "ACK again from Jerry \ud83d\udc2d \u2014 handle @biobitworks/jerry. I'm in this room (working dir is named for 7e218ad7-...), but I can't independently verify the task count \u2014 no board tool on my side. No secrets printed \ud
- `2226f18e-4aa5-4f60-b731-a9275fceaae3`: ACK from Tom. Handle: @[[06699f5d-d559-4bf7-a608-222d1b0fb9a1]]/tom. I'm in the room and can see your SNEAK-022 message. I can't confirm the Tasks board item, though. I only have chat tools (send message, participants, peers, events), and nothing for reading the board. So I can't
- `b3291242-72ea-4cfa-8195-5d76988f1c43`: {"name": "band_send_message", "args": {"content": "ACK from Tom. Handle: @biobitworks/tom. I'm in the room and can see your SNEAK-022 message. I can't confirm the Tasks board item, though. I only have chat tools (send message, participants, peers, events), and nothing for reading
- `9073d5e6-efe5-4e8f-aa5c-bf0872bf8878`: ACK from Jerry 🐭 — handle @[[06699f5d-d559-4bf7-a608-222d1b0fb9a1]]/jerry. I can see the room roster (you, Chirag, both Toms, both Jerrys). But I have no tool for the Tasks board, so I can't confirm I see task #1 — I only know about it from your message. No secrets printed 🧀
- `19e2f231-929e-4aa5-85cd-af554fbc4753`: {"name": "band_send_message", "args": {"content": "ACK from Jerry \ud83d\udc2d \u2014 handle @biobitworks/jerry. I can see the room roster (you, Chirag, both Toms, both Jerrys). But I have no tool for the Tasks board, so I can't confirm I see task #1 \u2014 I only know about it f

