# The Bifrost gateway, beside the LiteLLM one

Why this exists at all -- what Bifrost routes differently and what it would cost
to switch -- is [`docs/bifrost.md`](../../../docs/bifrost.md). This file is the
field-by-field reading of `config.json`, which is JSON and so has nowhere to put
a comment.

It listens on **8081**, not 4000, so it can be up at the same time as
`just ops::gateway` and the same task can be run through both.

```
just ops::bifrost
GATEWAY_URL=http://host.docker.internal:8081/litellm/v1 \
GATEWAY_API_KEY=sk-bf-local-dev \
  just eval incremental-dupes
```

`aws sso login` first: the container signs for Bedrock with your own credentials,
exactly as the LiteLLM one does.

## config.json, field by field

### `client.allowed_headers`

Claude Code sends `anthropic-beta`, `anthropic-version` and `x-api-key`, and
Bifrost rejects headers it was not told to accept. Without this list the harness
fails authentication rather than reporting a bad model or a bad key, which is the
kind of error that reads like anything except a header allowlist. Bifrost's own
Claude Code runbook leads with this step.

### `client.enforce_auth_on_inference`

On, so a request has to carry a virtual key. Off would be simpler locally and
would also mean the local gateway is a different thing from the deployed one in
the one respect -- who is allowed to spend -- where they must not differ.

### `client.compat`

`should_drop_params` is the `drop_params: true` of the LiteLLM config: a harness
sending a parameter this model does not support gets served rather than 400'd.
It is off by default in Bifrost, which is the opposite of LiteLLM's habit here.

It also carries the rule `hooks.py` exists for. Bifrost's compat plugin models
`reasoning_with_tool_calls` as a model capability and drops reasoning when tools
are present and the capability is missing -- but only on chat completions, which
is the only surface where that is true of this model. On the responses surface,
where Claude Code's requests land, the two travel together.

`convert_chat_to_responses` is left **off**. It rewrites chat-completion requests
into responses ones for models that only serve responses, and this model serves
both; turning it on would silently move every harness that speaks chat
completions -- aider, opencode, the baseline agent -- onto a surface none of them
has been measured against.

### `providers.bedrock_mantle.keys[].value: ""`

Empty on purpose. An empty key value is what selects SigV4 over a bearer token:
`mantleSigner` returns a signer when `key.Value` is empty and `nil` when it is
set, and signing runs through the AWS SDK's default credential chain. Locally
that is your `~/.aws`; deployed it would be the ECS task role, with nothing to
rotate. The signing service is `bedrock-mantle`, so the IAM grant is the same
`bedrock-mantle:CreateInference` on the project ARN that the LiteLLM gateway
already holds.

### `aliases.gemma`

Harnesses ask for `gemma` (`agent.yaml`, `ops/canary/agents.yaml`) and the
endpoint serves `google.gemma-4-31b`. The long form rather than the one-line
`"gemma": "google.gemma-4-31b"` because two of its fields are load-bearing:

- `model_name` is what pricing and logs attribute against, and Bifrost's catalog
  prices `google.gemma-4-31b` -- at the same $0.14/$0.40 per million this
  repository hardcoded into the LiteLLM config -- so the spend column fills
  itself in only if the canonical name is spelled out.
- `model_id` is also what the URL builder gates on. Bifrost puts Gemma 4 and
  gpt-5.x under `openai/v1` and gpt-oss under bare `v1`; a model string that does
  not resolve to something containing `gemma-4` builds the wrong path and the
  endpoint answers 404 for a model that is definitely there.

No provider prefix is needed on the wire. Bifrost auto-resolves the provider when
the model name carries none, and there is exactly one provider here.

### `governance.virtual_keys`

One seeded key so a local run has something to authenticate with, in the shape a
deployed one would use: keys as config rather than as rows created by a terraform
provider that authenticates at plan time.

The value comes from `BIFROST_VIRTUAL_KEY` and **must start with `sk-bf-`**.
Bifrost accepts any shape on its own `x-bf-vk` header and only the `sk-bf-`
prefix on `Authorization` and `x-api-key`, which are the two headers every
harness here actually sends. The compose file defaults it to `sk-bf-local-dev`,
matching `sk-local-dev` on the LiteLLM side.

### How this file was checked

Bifrost ships its own `transports/config.schema.json`, and this config validates
against it. That is worth doing before a container ever starts, because the
schema is strict about `additionalProperties` on `client`, `client.compat`,
`logs_store`, `bedrock_mantle_key_config` and each virtual key -- so a
misremembered field name is a validation error rather than a setting that is
silently ignored. The provider-key object is the one permissive spot; its fields
here come from Bifrost's Bedrock Mantle page verbatim.

The schema is an editor and CI artifact, not a startup check: Bifrost does not
validate `config.json` against it at runtime, and it lags the Go types in places
(its `model_family` enum is missing `gemma`, which the loader accepts). Family is
left to be inferred from `model_name` instead, which lands on Gemma by substring
either way.

## Why `/litellm` in the URL

Bifrost namespaces every ingress -- there is no bare `/v1/chat/completions`. The
`/litellm` prefix registers both the OpenAI and the Anthropic route sets, so:

| Harness reads | Value |
|---|---|
| `OPENAI_BASE_URL` | `http://host.docker.internal:8081/litellm/v1` |
| `ANTHROPIC_BASE_URL` | `http://host.docker.internal:8081/litellm` |

which is exactly the `${GW%/v1}` relationship the justfile already derives. One
variable changes and nothing else in the plumbing moves. `/openai/v1` and
`/anthropic` work too, if you would rather be explicit than compatible.

The one thing `/litellm` does not register is list-models, so
`CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY` would 404 there. It is off by
default, and Claude Code ignores any discovered model whose id does not begin
with `claude` or `anthropic`, so `gemma` could not be discovered in any case.

## What is not covered here

The 18-tool cap. Nothing in Bifrost trims a tool list by count, and its extension
points are a compiled Go plugin or the deprecated WASM path -- both heavier than
the Python callback in `hooks.py`. Measure whether the cap even applies on the
responses surface before writing one: it was binary-searched on chat completions,
and Claude Code's 28 tools have never been put to `/responses`.
