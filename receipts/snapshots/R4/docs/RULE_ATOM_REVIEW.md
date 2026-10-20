# Rule atom review

All nonempty extracted text lines are independently addressed. Exact original PDF bytes and predecessor text are preserved. This is a complete line inventory of the supplied extraction, not a new PDF extraction or a visual/table-layout audit. Wrapped lines are source atoms, not necessarily standalone requirements. Numeric values and labels remain inside their original line context. Content identity is separate from occurrence/context identity. No source instructions are executed.

| Atom | PDF page | Scope | Exact extracted line |
|---|---:|---|---|
| RULE-P01-L001 | 1 | purpose/core overview | SF Startup Challenge Hackathon |
| RULE-P01-L004 | 1 | purpose/core overview | Date: October 20, 2026 · AWS Builder Loft &#124; Theme: Build an |
| RULE-P01-L005 | 1 | purpose/core overview | AI-Native Startup Run by a Team of Agents, Using Band Desktop |
| RULE-P01-L006 | 1 | purpose/core overview | and Cognee |
| RULE-P01-L008 | 1 | purpose/core overview | The next startup won't be one founder and one chatbot. It will be one founder leading a team of |
| RULE-P01-L009 | 1 | purpose/core overview | AI agents: a planner, builders, a reviewer, and a security lead. They share one plan, hand work |
| RULE-P01-L010 | 1 | purpose/core overview | to each other, remember what they learned yesterday, and ask the human only when a real |
| RULE-P01-L011 | 1 | purpose/core overview | decision is needed. |
| RULE-P01-L014 | 1 | purpose/core overview | The SF Startup Challenge asks you to build that kind of company. Use Band Desktop so your |
| RULE-P01-L015 | 1 | purpose/core overview | agents work as a coordinated team, and Cognee so they have lasting memory. Then ship a real |
| RULE-P01-L016 | 1 | purpose/core overview | product that solves a real startup problem. Bonus points if your product can charge for itself |
| RULE-P01-L017 | 1 | purpose/core overview | with Flexprice, and if your agents ship secure code with Snyk. |
| RULE-P01-L020 | 1 | purpose/core overview | Core Challenge |
| RULE-P01-L022 | 1 | purpose/core overview | Design and build an agentic product (or an agent-powered startup workflow) that: |
| RULE-P01-L025 | 1 | purpose/core overview |     ●​ Band Desktop: Runs your agents as one collaborative team in a shared room. They |
| RULE-P01-L026 | 1 | purpose/core overview |       work from one plan, claim and finish work items, @mention each other to pass context, |
| RULE-P01-L027 | 1 | purpose/core overview |       and bring decisions to the human in one place. |
| RULE-P01-L028 | 1 | purpose/core overview |     ●​ Cognee: Gives your agents an AI memory that lasts across sessions, restarts, and |
| RULE-P01-L029 | 1 | purpose/core overview |        agents. Your team remembers customers, decisions, code context, and lessons learned |
| RULE-P01-L030 | 1 | purpose/core overview |        instead of starting from zero every time. |
| RULE-P01-L031 | 1 | purpose/core overview |     ●​  Flexprice (bonus): Meters usage and bills for it with usage-based, credit-based, or |
| RULE-P01-L032 | 1 | purpose/core overview |        hybrid pricing, so your startup has a real business model from day one. |
| RULE-P01-L033 | 1 | purpose/core overview |     ●​ Snyk (bonus): Scans the code, dependencies, and containers your agents produce, so |
| RULE-P01-L034 | 1 | purpose/core overview |       a security check is built into how your agent team ships. |
| RULE-P02-L001 | 2 | mandatory integration | Mandatory Requirements |
| RULE-P02-L004 | 2 | mandatory integration | 1. Band Desktop integration (new desktop features) |
| RULE-P02-L006 | 2 | mandatory integration | Your project must use Band Desktop, BAND's new desktop app for coordinating coding agents, |
| RULE-P02-L007 | 2 | mandatory integration | as the coordination layer for your agent team. At minimum: |
| RULE-P02-L010 | 2 | mandatory integration |     ●​ Shared room: Two or more agents work together in one Band room. Using agents from |
| RULE-P02-L011 | 2 | mandatory integration |         different harnesses or frameworks (for example Claude Code with Codex, Copilot, |
| RULE-P02-L012 | 2 | mandatory integration |       OpenCode, or a LangGraph/CrewAI agent) scores higher. |
| RULE-P02-L013 | 2 | mandatory integration |     ●​ One plan, one board: A lead or architect agent writes the plan in the room. Agents claim |
| RULE-P02-L014 | 2 | mandatory integration |       work items and move them from To-do to Done. |
| RULE-P02-L015 | 2 | mandatory integration |     ●​  Agent-to-agent handoffs: Agents @mention each other and pass context directly, with |
| RULE-P02-L016 | 2 | mandatory integration |       no human copy-pasting between them. |
| RULE-P02-L017 | 2 | mandatory integration |     ●​ Human in the loop: At least one real decision or approval (for example running a |
| RULE-P02-L018 | 2 | mandatory integration |       command, editing a file, or a product choice) goes to the human through Band instead |
| RULE-P02-L019 | 2 | mandatory integration |        of being hard-coded. |
| RULE-P02-L020 | 2 | mandatory integration |     ●​  Visibility: Your demo must show Band Desktop's views of the work: rooms, the work |
| RULE-P02-L021 | 2 | mandatory integration |        board, and per-agent sessions, tokens, and estimated cost. |
| RULE-P02-L024 | 2 | mandatory integration | 2. Cognee integration (AI memory) |
| RULE-P02-L026 | 2 | mandatory integration | Your agents must use Cognee Open Source as working memory, not as a static document |
| RULE-P02-L027 | 2 | mandatory integration | dump. At minimum: |
| RULE-P02-L030 | 2 | mandatory integration |     ●​ Agents write to memory during the work (for example decisions, customer insights, |
| RULE-P02-L031 | 2 | mandatory integration |       code context, or review findings). |
| RULE-P02-L032 | 2 | mandatory integration |     ●​ Agents recall from memory to change what they do next, and you must show this |
| RULE-P02-L033 | 2 | mandatory integration |        across a session restart or between two different agents. |
| RULE-P02-L034 | 2 | mandatory integration |     ●​  Using improve or forget, or connecting Cognee to a graph backend such as Neo4j, |
| RULE-P02-L035 | 2 | mandatory integration |        earns extra credit within this criterion. |
| RULE-P02-L038 | 2 | mandatory integration | 3. Deep integration |
| RULE-P02-L040 | 2 | mandatory integration | Band Desktop and Cognee must be essential to the product. If you can remove either one and |
| RULE-P02-L041 | 2 | mandatory integration | the demo still works the same way, it's bolted on. Integrations that feel like afterthoughts are |
| RULE-P02-L042 | 2 | mandatory integration | grounds for disqualification. |
| RULE-P03-L001 | 3 | bonus / technology primer | Bonus Integrations (Extra Marks) |
| RULE-P03-L004 | 3 | bonus / technology primer | Flexprice: Usage-based billing |
| RULE-P03-L006 | 3 | bonus / technology primer | Use Flexprice to meter real usage events from your product or agents (API calls, tokens, tasks |
| RULE-P03-L007 | 3 | bonus / technology primer | completed, reports generated) and turn them into a pricing model: usage-based, credits and |
| RULE-P03-L008 | 3 | bonus / technology primer | top-ups, tiered, or hybrid. Top marks go to projects where metering drives the product, for |
| RULE-P03-L009 | 3 | bonus / technology primer | example credits that gate features, or agent costs from Band passed through to customer |
| RULE-P03-L010 | 3 | bonus / technology primer | billing. |
| RULE-P03-L013 | 3 | bonus / technology primer | Snyk: Secure by default |
| RULE-P03-L015 | 3 | bonus / technology primer | Use Snyk (CLI, Snyk Code, Snyk Open Source, or Snyk Container) to scan what your agents |
| RULE-P03-L016 | 3 | bonus / technology primer | build. Top marks go to projects where security is a team member, for example a |
| RULE-P03-L017 | 3 | bonus / technology primer | security-reviewer agent in the Band room that runs Snyk scans, posts findings, blocks a work |
| RULE-P03-L018 | 3 | bonus / technology primer | item until it's fixed, and stores recurring issues in Cognee so the team stops repeating them. |
| RULE-P03-L021 | 3 | bonus / technology primer | Technology Primers |
| RULE-P03-L023 | 3 | bonus / technology primer |     ●​ Band Desktop (Mission control for agent teams): BAND is interaction infrastructure |
| RULE-P03-L024 | 3 | bonus / technology primer |         that lets AI agents and humans collaborate in shared rooms, whatever framework each |
| RULE-P03-L025 | 3 | bonus / technology primer |        agent runs on. Band Desktop (with the jam CLI) is the new desktop app that brings your |
| RULE-P03-L026 | 3 | bonus / technology primer |         local coding agents into one workspace. It includes shared rooms, a plan and work-item |
| RULE-P03-L027 | 3 | bonus / technology primer |        board, a Human in the loop column, predefined teams like Feature crew or Bug squad, |
| RULE-P03-L028 | 3 | bonus / technology primer |          filterable activity trails, approvals before commands or file edits, and sessions, tokens, |
| RULE-P03-L029 | 3 | bonus / technology primer |       and cost per agent. Your agents keep running on your machine in your own harness; |
| RULE-P03-L030 | 3 | bonus / technology primer |      BAND carries the messages between them. |
| RULE-P03-L031 | 3 | bonus / technology primer |     ●​ Cognee (AI memory for agents): Cognee turns conversations, documents, and context |
| RULE-P03-L032 | 3 | bonus / technology primer |         into a knowledge-graph "AI brain" that agents, apps, and users can query across |
| RULE-P03-L033 | 3 | bonus / technology primer |        sessions. Add data, cognify it into memory, and search it from any agent. For this |
| RULE-P03-L034 | 3 | bonus / technology primer |        hackathon, use Cognee Open Source. |
| RULE-P03-L035 | 3 | bonus / technology primer |     ●​  Flexprice (Open-source usage-based billing - bonus): Flexprice is an open-source, |
| RULE-P03-L036 | 3 | bonus / technology primer |         developer-first platform for metering, billing, and feature access. Send usage events, |
| RULE-P03-L037 | 3 | bonus / technology primer |       and it handles aggregation, credits, entitlements, and invoicing for usage-based, |
| RULE-P03-L038 | 3 | bonus / technology primer |        seat-based, or hybrid pricing. Use the cloud version or self-host it. |
| RULE-P03-L039 | 3 | bonus / technology primer |     ●​ Snyk (Developer security - bonus): Snyk finds and helps fix vulnerabilities in your |
| RULE-P03-L040 | 3 | bonus / technology primer |        code, open-source dependencies, containers, and infrastructure-as-code. It runs from |
| RULE-P03-L041 | 3 | bonus / technology primer |        the CLI, your IDE, or CI. |
| RULE-P04-L001 | 4 | suggested track / table |   Suggested Problem Tracks |
| RULE-P04-L004 | 4 | suggested track / table | Track Name                    Summary                              Architectural Details |
| RULE-P04-L006 | 4 | suggested track / table | 1. One-Founder Software Studio    Solo founders spend their time     Band Desktop: a Feature-crew |
| RULE-P04-L007 | 4 | suggested track / table |                                  passing context between coding   room (planner, backend, |
| RULE-P04-L008 | 4 | suggested track / table |                                  agents instead of building.          frontend, reviewer) that ships |
| RULE-P04-L009 | 4 | suggested track / table |                                                                         features from one plan.Cognee: |
| RULE-P04-L010 | 4 | suggested track / table |                                                            remembers the codebase, past |
| RULE-P04-L011 | 4 | suggested track / table |                                                                          decisions, and review findings |
| RULE-P04-L012 | 4 | suggested track / table |                                                                    across sessions.Snyk: a security |
| RULE-P04-L013 | 4 | suggested track / table |                                                                  agent gates merges.Flexprice: |
| RULE-P04-L014 | 4 | suggested track / table |                                                                 meters builds per customer |
| RULE-P04-L015 | 4 | suggested track / table |                                                                               project. |
| RULE-P04-L017 | 4 | suggested track / table | 2. Autonomous GTM Team          Early startups can't afford        Band Desktop: a researcher, |
| RULE-P04-L018 | 4 | suggested track / table |                                   separate research, outbound,       copywriter, and qualifier agent |
| RULE-P04-L019 | 4 | suggested track / table |                               and CRM staff.                  hand leads to each other; the |
| RULE-P04-L020 | 4 | suggested track / table |                                                                   founder approves |
| RULE-P04-L021 | 4 | suggested track / table |                                                                sends.Cognee: memory of every |
| RULE-P04-L022 | 4 | suggested track / table |                                                                       prospect, objection, and |
| RULE-P04-L023 | 4 | suggested track / table |                                                                            reply.Flexprice: credits per |
| RULE-P04-L024 | 4 | suggested track / table |                                                                    enriched lead. |
| RULE-P04-L026 | 4 | suggested track / table | 3. AI Customer Success Squad     Support tickets bounce between   Band Desktop: triage, billing, and |
| RULE-P04-L027 | 4 | suggested track / table |                                       tools and lose context at every      technical specialist agents share |
| RULE-P04-L028 | 4 | suggested track / table |                                     handoff.                       one room per case, and humans |
| RULE-P04-L029 | 4 | suggested track / table |                                                                      step in for refunds.Cognee: |
| RULE-P04-L030 | 4 | suggested track / table |                                                                customer history and known |
| RULE-P04-L031 | 4 | suggested track / table |                                                                             fixes.Flexprice: shows usage |
| RULE-P04-L032 | 4 | suggested track / table |                                                            and invoice context to the billing |
| RULE-P04-L033 | 4 | suggested track / table |                                                                        agent. |
| RULE-P04-L035 | 4 | suggested track / table | 4. Secure Ship Pipeline             Agent-written code ships fast,     Band Desktop: coder, test, and |
| RULE-P04-L036 | 4 | suggested track / table |                               and so do its vulnerabilities.         security-reviewer agents on one |
| RULE-P04-L037 | 4 | suggested track / table |                                                                   board.Snyk: scans every work |
| RULE-P04-L038 | 4 | suggested track / table |                                                                      item before Done.Cognee: |
| RULE-P04-L039 | 4 | suggested track / table |                                                            remembers vulnerability patterns |
| RULE-P04-L040 | 4 | suggested track / table |                                                            and fixes so they aren't repeated. |
| RULE-P05-L001 | 5 | suggested track / judging | Track Name                    Summary                              Architectural Details |
| RULE-P05-L003 | 5 | suggested track / judging | 5. Usage-Billed AI API in a Day     Launching a paid AI API means     Band Desktop: an agent team |
| RULE-P05-L004 | 5 | suggested track / judging |                                      building metering, credits, and       builds the API, tests, and |
| RULE-P05-L005 | 5 | suggested track / judging |                                            limits from scratch.                 docs.Flexprice: metering, free |
| RULE-P05-L006 | 5 | suggested track / judging |                                                                                                     tier, overages, and |
| RULE-P05-L007 | 5 | suggested track / judging |                                                                      credits.Cognee: remembers |
| RULE-P05-L008 | 5 | suggested track / judging |                                                                            pricing experiments and |
| RULE-P05-L009 | 5 | suggested track / judging |                                                                customer feedback. |
| RULE-P05-L011 | 5 | suggested track / judging | 6. Investor & Fundraise Copilot     Founders lose track of investor     Band Desktop: a research agent, |
| RULE-P05-L012 | 5 | suggested track / judging |                                    conversations, intros, and         a deck-and-memo agent, and a |
| RULE-P05-L013 | 5 | suggested track / judging |                                     follow-ups.                        follow-up agent coordinate in a |
| RULE-P05-L014 | 5 | suggested track / judging |                                                                        fundraise room.Cognee: |
| RULE-P05-L015 | 5 | suggested track / judging |                                                                              relationship memory for every |
| RULE-P05-L016 | 5 | suggested track / judging |                                                                                investor, meeting, and promise. |
| RULE-P05-L018 | 5 | suggested track / judging | 7. Incident War Room               On-call is a human copying logs    Band Desktop: detector, |
| RULE-P05-L019 | 5 | suggested track / judging |                               between tools at 3am.              root-cause, and fix agents in one |
| RULE-P05-L020 | 5 | suggested track / judging |                                                                           incident room, with human |
| RULE-P05-L021 | 5 | suggested track / judging |                                                                     approval before |
| RULE-P05-L022 | 5 | suggested track / judging |                                                                 deploys.Cognee: remembers |
| RULE-P05-L023 | 5 | suggested track / judging |                                                                      past incidents and |
| RULE-P05-L024 | 5 | suggested track / judging |                                                                  runbooks.Snyk: checks the fix |
| RULE-P05-L025 | 5 | suggested track / judging |                                                                     before rollout. |
| RULE-P05-L027 | 5 | suggested track / judging | 8. Startup Knowledge OS (LLM    Company knowledge is spread     Cognee: builds and maintains a |
| RULE-P05-L028 | 5 | suggested track / judging | Wiki)                            across docs, chats, and people's     living company wiki.Band |
| RULE-P05-L029 | 5 | suggested track / judging |                                  heads.                          Desktop: curator and Q&A |
| RULE-P05-L030 | 5 | suggested track / judging |                                                                   agents keep it current and route |
| RULE-P05-L031 | 5 | suggested track / judging |                                                                     questions to the right owner. |
| RULE-P05-L033 | 5 | suggested track / judging | 9. Open Innovation              Any startup problem where        Use Band Desktop for team |
| RULE-P05-L034 | 5 | suggested track / judging |                                  agents need to work as a team      coordination and Cognee for |
| RULE-P05-L035 | 5 | suggested track / judging |                               and remember.                  memory. Add Flexprice and |
| RULE-P05-L036 | 5 | suggested track / judging |                                                          Snyk for bonus marks. |
| RULE-P05-L039 | 5 | suggested track / judging |   Judging Criteria |
| RULE-P05-L041 | 5 | suggested track / judging |           ●​ Band Desktop integration (25%): Real multi-agent collaboration, plan and board, |
| RULE-P05-L042 | 5 | suggested track / judging |              handoffs, human-in-the-loop. |
| RULE-P06-L001 | 6 | judging / deliverables / setup / unresolved publication |     ●​ Cognee integration (25%): Memory that changes agent behavior across sessions and |
| RULE-P06-L002 | 6 | judging / deliverables / setup / unresolved publication |        agents. |
| RULE-P06-L003 | 6 | judging / deliverables / setup / unresolved publication |     ●​  Startup viability (20%): Real problem, clear user, believable business. |
| RULE-P06-L004 | 6 | judging / deliverables / setup / unresolved publication |     ●​  Technical execution and demo quality (20%) |
| RULE-P06-L005 | 6 | judging / deliverables / setup / unresolved publication |     ●​  Innovation and creativity (10%) |
| RULE-P06-L006 | 6 | judging / deliverables / setup / unresolved publication |     ●​  Flexprice integration (Bonus - up to +10%) |
| RULE-P06-L007 | 6 | judging / deliverables / setup / unresolved publication |     ●​ Snyk integration (Bonus - up to +10%) |
| RULE-P06-L009 | 6 | judging / deliverables / setup / unresolved publication | Submission & Deliverables |
| RULE-P06-L012 | 6 | judging / deliverables / setup / unresolved publication | What to submit: |
| RULE-P06-L014 | 6 | judging / deliverables / setup / unresolved publication |     ●​ Working prototype: Live or local demo. |
| RULE-P06-L015 | 6 | judging / deliverables / setup / unresolved publication |     ●​ Source code: Repository link. |
| RULE-P06-L016 | 6 | judging / deliverables / setup / unresolved publication |     ●​ Demo video (required, 2–3 min): Must show Band Desktop in action (the room, the |
| RULE-P06-L017 | 6 | judging / deliverables / setup / unresolved publication |       work board moving, a human decision, and the cost view) and a Cognee memory recall |
| RULE-P06-L018 | 6 | judging / deliverables / setup / unresolved publication |        changing what an agent does. |
| RULE-P06-L019 | 6 | judging / deliverables / setup / unresolved publication |     ●​  Project description: The problem, your agent team (roles, harnesses, and how they |
| RULE-P06-L020 | 6 | judging / deliverables / setup / unresolved publication |       hand off), how you use Cognee memory, and whether you used Flexprice or Snyk and |
| RULE-P06-L021 | 6 | judging / deliverables / setup / unresolved publication |        how. |
| RULE-P06-L022 | 6 | judging / deliverables / setup / unresolved publication |     ●​  Pitch deck: Optional. |
| RULE-P06-L024 | 6 | judging / deliverables / setup / unresolved publication | Setup Checklist - Hacker Guide |
| RULE-P06-L026 | 6 | judging / deliverables / setup / unresolved publication |     ●​ Band Desktop: Download it from band.ai/download, sign in at app.band.ai, and |
| RULE-P06-L027 | 6 | judging / deliverables / setup / unresolved publication |         follow the setup guide at docs.band.ai/jam (CLI: brew install |
| RULE-P06-L028 | 6 | judging / deliverables / setup / unresolved publication |       thenvoi/tap/jam). Connect your first two agents to a room before you start building. |
| RULE-P06-L029 | 6 | judging / deliverables / setup / unresolved publication |        (https://www.band.ai/hacker-guide) |
| RULE-P06-L030 | 6 | judging / deliverables / setup / unresolved publication |     ●​ Cognee: Install Cognee Open Source from github.com/topoteretes/cognee and |
| RULE-P06-L031 | 6 | judging / deliverables / setup / unresolved publication |        configure your LLM and storage (optionally Neo4j as the graph store). Sketch which |
| RULE-P06-L032 | 6 | judging / deliverables / setup / unresolved publication |       memories your agents will write and read. |
| RULE-P06-L033 | 6 | judging / deliverables / setup / unresolved publication |     ●​  Flexprice (bonus): Sign up or self-host (docs.flexprice.io), define your meters and |
| RULE-P06-L034 | 6 | judging / deliverables / setup / unresolved publication |         plan, and send a test usage event. |
| RULE-P06-L035 | 6 | judging / deliverables / setup / unresolved publication |     ●​ Snyk (bonus): Create a free account at snyk.io, install the Snyk CLI, run snyk auth, |
| RULE-P06-L036 | 6 | judging / deliverables / setup / unresolved publication |        then snyk test / snyk code test on your repo. |
| RULE-P06-L040 | 6 | judging / deliverables / setup / unresolved publication | What to fill in or check before publishing: |
| RULE-P06-L042 | 6 | judging / deliverables / setup / unresolved publication |     ●​ The placeholders for deadline, submission link, and support channel. |
| RULE-P07-L001 | 7 | unresolved publication checklist | ●​ Whether sponsors are giving promo codes or credits (like HackwithBay's Butterbase |
| RULE-P07-L002 | 7 | unresolved publication checklist |     code). |
| RULE-P07-L003 | 7 | unresolved publication checklist | ●​ The judging weights, if sponsors have their own expectations. |
| RULE-P07-L004 | 7 | unresolved publication checklist | ●​ The Band Desktop features I named come from BAND's own product page: agents |
| RULE-P07-L005 | 7 | unresolved publication checklist |     claim work items and move them from To-do to Done, agents can ask a person to |
| RULE-P07-L006 | 7 | unresolved publication checklist |    approve before they run a command or edit a file, right in the room, and the app shows |
| RULE-P07-L007 | 7 | unresolved publication checklist |     sessions, tokens, and estimated cost for every agent and every room. It's worth |
| RULE-P07-L008 | 7 | unresolved publication checklist |     confirming with the BAND team that they want the demo to show these specific |
| RULE-P07-L009 | 7 | unresolved publication checklist |     features. |
| RULE-P07-L010 | 7 | unresolved publication checklist | ●​  Older references to "Jam Desktop" now appear as BAND Desktop. The hacker guide |
| RULE-P07-L011 | 7 | unresolved publication checklist |    describes Jam Desktop as the app you download, and the jam CLI as the command-line |
| RULE-P07-L012 | 7 | unresolved publication checklist |     client it installs and keeps up to date. |
