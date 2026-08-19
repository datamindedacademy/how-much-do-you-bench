# Claude Code on Gemma, through Bifrost instead of LiteLLM

Claude Code is the harness we cannot make work. It reaches the model and every
request returns 200, but it does not finish: 168 turns, 1.5M input tokens,
$7.93, and a one-line bug still there at the end. It reads and re-plans without
acting. [`docs/harnesses.md`](harnesses.md) records that as fragility; this
document argues it is a consequence of the route its requests take, and that a
different gateway takes a different route.

Nothing here has been run against the deployed model. Everything about Bifrost
is read from its source at
[`maximhq/bifrost@1eaa684`](https://github.com/maximhq/bifrost) (2026-08-19) and
from its own documentation; everything about the model and the endpoint is
quoted from what this repository already measured. The only thing actually
executed is that the config in `ops/gateway/bifrost/` validates against Bifrost's
own `config.schema.json`. [Verifying the rest](#verifying-it) costs a bench run.

## The one-sentence version

Bifrost's Anthropic ingress converts `/v1/messages` into a **Responses** request,
and its `bedrock_mantle` provider serves Gemma on `/openai/v1/responses` -- the
one surface of this endpoint that takes tools and reasoning together, and the
only one that returns reasoning content at all. LiteLLM converts the same
request into a **chat completion**, which is the surface that refuses the
combination, which is why `ops/gateway/hooks.py` has to throw the reasoning away
to keep the tools.

## Why the current route hurts this harness

Three facts, each of them already established here:

1. Gemma on mantle serves tools and reasoning together **only** on
   `/v1/responses`. Chat Completions rejects the combination outright
   (`ops/README.md`, "Constraints worth knowing").
2. Reasoning content comes back **only** from the Responses API. Chat
   Completions never returns it.
3. LiteLLM's `/v1/messages` adapter lands on chat completions, so
   `hooks.py` pins `reasoning_effort: "none"` and drops `thinking`, with the
   comment that "tools win over reasoning, because a data engineering agent that
   cannot run a command is useless while one that cannot think out loud is
   merely worse".

That trade is right given the route. The problem is that it is a trade at all.
Claude Code is a harness whose planning happens in thinking blocks: it decides
what to do while thinking and then emits the tool call. Serve it a model that
has been told not to think and it does its planning in assistant text instead --
which is exactly the observed failure, an agent that reads and re-plans in prose
without acting. Every one of those turns is also a turn whose reasoning cannot
be replayed on the next request, because chat completions did not return any.

There is a second, narrower LiteLLM problem worth naming since it is the one
that usually gets blamed: even when reasoning *is* allowed through, LiteLLM's
`/v1/messages` adapter drops `reasoning_content` on the floor rather than
re-emitting it as `thinking` blocks for OpenAI-compatible chat-completions
backends ([BerriAI/litellm#29518](https://github.com/BerriAI/litellm/issues/29518)).
Its OpenAI parser fills `Message.reasoning_content` and sets
`thinking_blocks=None`, and the Anthropic translator only reads the latter. So
the "just turn reasoning back on" fix does not work on this route either: the
thinking would be generated, billed, and then discarded in translation.

## What Bifrost does differently

### The ingress converts to Responses, not to chat

`transports/bifrost-http/integrations/anthropic.go` registers `/v1/messages`
with `GetHTTPRequestType` returning `schemas.ResponsesRequest` and a converter
calling `ToBifrostResponsesRequest`. There is no chat-completions detour: an
Anthropic-format request is a Responses request from the first hop.

### The provider knows this endpoint, including this model

Bifrost has a `bedrock_mantle` provider distinct from its `bedrock` one --
`core/providers/bedrockmantle/`. It is not a generic OpenAI-compatible shim
pointed at a base URL; it knows the shape of the endpoint:

| What it knows | Where |
|---|---|
| Host is `bedrock-mantle.{region}.api.aws` | `mantleHost` |
| Claude goes to `/anthropic/v1/messages`, everything else to the OpenAI surface | `ChatCompletion`, `Responses` |
| **Gemma 4 and gpt-5.x live under `openai/v1`, gpt-oss under bare `v1`** | `mantleOpenAIURL` |
| SigV4 signs for service `bedrock-mantle` | `bedrockMantleSigningService` |
| Credentials come from `config.LoadDefaultConfig` -- the AWS SDK default chain | `bedrock/signer.go` |

That third row is the one that would otherwise cost a day: a custom
OpenAI-compatible provider pointed at `https://bedrock-mantle.eu-central-1.api.aws/v1`
would 404 for Gemma, because Gemma is served one path segment further along.

The default chain means the deployed gateway authenticates as its ECS task role
exactly as it does today. The IAM grant is unchanged --
`bedrock-mantle:CreateInference` on the project ARN -- because it is the same
signing service against the same host.

### `thinking` survives the trip

`ToBifrostResponsesRequest` (`core/providers/anthropic/responses.go`) maps:

| Claude Code sends | Bifrost produces | Mantle receives |
|---|---|---|
| `max_tokens` (required by the Anthropic API) | `params.MaxOutputTokens` | `max_output_tokens` -- **which this model accepts** |
| `thinking: {type: "enabled", budget_tokens}` | `reasoning: {effort, max_tokens, summary}` | `reasoning` alongside `tools` |
| `thinking: {type: "disabled"}` | `reasoning: {effort: "none"}` | reasoning off, explicitly |
| no `thinking` at all | no `reasoning` parameter | endpoint default |

The `max_tokens` row is its own small win. `hooks.py` drops `max_tokens` and
`max_completion_tokens` because the model rejects both, and then fills in
`max_output_tokens` by hand on the responses path because codex sent none and
its stream ended with `reason: max_output_tokens` mid tool call. Bifrost's
mapping does that translation as a matter of course: the Anthropic spelling
becomes the responses spelling, which is the one spelling this model takes.

Bifrost also detects Claude Code by user agent (`IsClaudeCodeRequest`) and
forces `summary: "detailed"`, and its `anthropic` package carries a wall of
tests named for exactly this problem class -- `thinking_tokens_test.go`,
`reasoningdialect_test.go`, `reasoningreplay_test.go`,
`adaptivethinkingstrip_test.go`, `redactedthinking_test.go`,
`visiblethinkingresponses_test.go`. That is not proof it is correct against
Gemma. It is evidence the round trip is a thing someone maintains rather than a
thing that happens to work.

### Half of `hooks.py` becomes configuration

Bifrost ships a `compat` plugin (`plugins/compat/`) whose stated purpose is
"LiteLLM-compatible request normalization". It drops unsupported parameters
according to the model catalog, and its capability list includes
`reasoning_with_tool_calls` -- the exact constraint this endpoint imposes:

```go
if params.Reasoning != nil {
    // for chat completions, some models do not support reasoning_effort
    // with tools
    if !isSupported["reasoning"] || (hasSupportedTools && !isSupported["reasoning_with_tool_calls"]) {
```

So the rule `hooks.py` implements by hand -- if there are tools, there is no
reasoning -- is a capability flag in Bifrost, applied only on the surface where
it is true. It is off by default; `client.compat.should_drop_params` turns it
on.

Bifrost also prices `google.gemma-4-31b` in its own catalog, at the same
$0.14/$0.40 per million this repository hardcoded into `config.yaml`, with
`bedrock_mantle` falling back to `bedrock` pricing when there is no mantle-specific
row (`framework/modelcatalog/datasheet/cost_test.go`). The spend column does not
need a manual price table.

## What does not come for free

| `hooks.py` rule | Under Bifrost |
|---|---|
| Drop `max_tokens` / `max_completion_tokens` | Not needed on the responses route -- becomes `max_output_tokens` |
| Reasoning off when tools present | `compat` plugin + `reasoning_with_tool_calls` capability, and only where it applies |
| `parallel_tool_calls: false` | `compat` plugin, if the catalog marks it unsupported for this model. Otherwise a catalog override |
| Strip `strict` from tool schemas | Not modelled as a capability. Unknown |
| **Trim 28 tools to 18** | **No equivalent. See below** |
| Drop `web_search` and other hosted tool types | Bifrost validates tools per provider, but not against this endpoint's list |

The tool trim is the gap. Nothing in Bifrost caps a tool list by count, and its
extension points are heavier than a Python callback: native Go plugins compiled
into a custom binary, or the deprecated WASM path. Before writing one, measure
whether the cap is a property of the endpoint or of the chat-completions surface
-- the 18-tool ceiling was binary-searched against a captured Claude Code request
on chat completions, and no harness here has ever put a list that long to
`/responses`. If the cap holds there too,
the cheap fix is not a plugin: it is telling Claude Code to offer fewer tools.

## Cost of the swap, beyond the model plumbing

The gateway is not only a translator here. It mints a virtual key per rollout,
meters it, and retires it (`ops/platform/worker/gateway.py`), and it holds one
key per team. Bifrost covers all of it, differently:

| Today (LiteLLM) | Bifrost |
|---|---|
| `POST /key/generate`, `/key/delete` | `POST`/`DELETE /api/governance/virtual-keys` |
| `GET /spend/logs?api_key=` summed per row | `GET /api/logs/stats?virtual_key_ids=` (`total_tokens`, `total_cost`) |
| Team keys via terraform's `ncecere/litellm` provider | `governance.virtual_keys[]` in `config.json`, seeded at startup |
| Requires Postgres for keys and spend | SQLite in the app dir; Postgres optional |
| Keys are `sk-...` | Keys **must** be `sk-bf-...` on `Authorization` / `x-api-key`; only the `x-bf-vk` header takes any other shape |

The `sk-bf-` prefix is load-bearing and would invalidate every issued team key.
Seeding keys from `config.json` also removes the two-pass terraform apply that
exists only because the litellm provider authenticates at plan time against a
gateway terraform is simultaneously creating.

Two smaller differences:

- **Every ingress is namespaced.** There is no bare `/v1/chat/completions`;
  routes are registered under `/openai`, `/anthropic`, `/genai`, `/litellm`,
  `/bedrock`, `/cohere`. The `/litellm` prefix registers both the OpenAI and the
  Anthropic route sets, which is what makes this a one-variable change: point
  `GATEWAY_URL` at `.../litellm/v1` and the existing `${GW%/v1}` in the justfile
  derives `.../litellm` as `ANTHROPIC_BASE_URL`, which is where
  `/litellm/v1/messages` lives. Nothing else in the plumbing moves.
- **Claude Code's headers must be allowed.** `client.allowed_headers` has to
  carry `anthropic-beta`, `anthropic-version`, `x-api-key` and friends or
  requests fail authentication. Bifrost's own Claude Code runbook leads with
  this.

`/litellm` does not register the list-models route, so
`CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY` would 404 there. Discovery is off
by default and Claude Code ignores any discovered model whose id does not start
with `claude` or `anthropic`, so `gemma` could never be discovered anyway.

## Running it

`ops/gateway/bifrost/` holds a local Bifrost beside the local LiteLLM rather than
instead of it -- it listens on 8081, so both can be up and the same task can be
run through each.

```
just ops::bifrost                                          # start it
GATEWAY_URL=http://host.docker.internal:8081/litellm/v1 \
GATEWAY_API_KEY=sk-bf-local-dev \
  just eval incremental-dupes                              # same task, other gateway
just view
```

The config is `ops/gateway/bifrost/config.json`, explained field by field in
`ops/gateway/bifrost/README.md` (JSON has nowhere to put a comment).

## Verifying it

In order, cheapest first. Each step is a thing that can fail, and the order is
chosen so a failure lands before the expensive step that depends on it.

1. **Does the endpoint answer at all through Bifrost?** One curl for
   `/litellm/v1/chat/completions` with `model: gemma`. Failure here is
   credentials, region, or the `openai/v1` path gate -- check that
   `ResolveCanonicalModel` sees `google.gemma-4-31b` and not the bare alias, or
   the request goes to `/v1/responses` instead of `/openai/v1/responses`.
2. **Does the tool cap apply on the responses surface?** Post to
   `/litellm/v1/responses` with 18 tools, then 19, then 28. This is the question
   the whole plan turns on: if 28 tools are fine there, Claude Code needs no
   trim at all and `hooks.py` has no unreplaced rule left.
3. **Do tools and reasoning coexist there?** Same request with
   `reasoning: {effort: "medium"}` and tools. `ops/README.md` says yes; nothing
   here has confirmed it through this path.
4. **Does a thinking block survive the round trip?** `just ops::canary` against
   the Bifrost URL, with `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING` **unset**, then
   read the trajectory for thinking content.
5. **Does it finish a task?** `just eval` on the one-line bug fix that produced
   the 168-turn run, with `claude-code` first in `agent.yaml`. Compare turns and
   input tokens against that measurement, not against the other harnesses.
6. **Only then**, the ops-side questions: per-rollout key mint/retire against
   `/api/governance/virtual-keys`, and whether `/api/logs/stats` settles the way
   `/spend/logs` does, or reports a number that is still moving.

If step 5 does not move the number, the hypothesis in this document is wrong and
the reasoning route was not what was holding Claude Code back. That is worth
knowing for the price of one eval.
