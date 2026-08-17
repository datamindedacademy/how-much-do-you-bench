"""Make tool-calling work for harnesses that ask for reasoning.

Gemma on Bedrock serves tools, and serves reasoning, but refuses both together
on /v1/chat/completions -- only /v1/responses allows the combination. Any
harness speaking the Anthropic API hits this: Claude Code always sends a
`thinking` block, LiteLLM turns that into `reasoning_effort` during
translation, and the request then arrives at the one endpoint that rejects it.

The model-level `reasoning_effort: "none"` in config.yaml cannot fix it,
because the translated value overwrites it. This runs later still -- after a
deployment is chosen, before the request goes out -- which is the first point
where the final parameters are visible.

Tools win over reasoning, because a data engineering agent that cannot run a
command is useless while one that cannot think out loud is merely worse.
"""

from typing import Any

from litellm.integrations.custom_logger import CustomLogger


class ToolsBeatReasoning(CustomLogger):
    async def async_pre_call_deployment_hook(
        self, kwargs: dict[str, Any], call_type: Any | None
    ) -> dict | None:
        if not kwargs.get("tools"):
            return None

        # `thinking` is the Anthropic spelling; it can survive translation.
        kwargs.pop("thinking", None)
        if kwargs.get("reasoning_effort") != "none":
            kwargs["reasoning_effort"] = "none"

        # This model returns one tool call per turn. Asking for several is not a
        # slow path, it is a 400 from the engine with no mention of which
        # parameter caused it.
        kwargs["parallel_tool_calls"] = False

        # Bedrock rejects strict tool schemas, and caps how many a request may
        # carry. A harness with a large toolset trips this and gets the same
        # unhelpful "Generation failed" as everything else.
        for tool in kwargs["tools"]:
            if isinstance(tool, dict):
                tool.pop("strict", None)
                fn = tool.get("function")
                if isinstance(fn, dict):
                    fn.pop("strict", None)
        return kwargs


proxy_handler_instance = ToolsBeatReasoning()
