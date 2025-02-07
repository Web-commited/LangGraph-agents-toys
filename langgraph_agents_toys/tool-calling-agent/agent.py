import boto3
from botocore.config import Config
import re
from typing import Dict, Callable, Optional, Tuple


class BedrockClient:
    def __init__(self, region_name: str = 'us-west-2'):
        self.config = Config(
            connect_timeout=120,
            read_timeout=120,
            retries={"max_attempts": 0}
        )
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=region_name,
            config=self.config,
        )


class ActionHandler:
    @staticmethod
    def calculate(expression: str) -> str:
        try:
            return str(eval(expression, {"__builtins__": {}}, {}))
        except Exception as e:
            return f"Calculation error: {str(e)}"

    @staticmethod
    def average_dog_weight(breed: str) -> str:
        weights = {
            "Scottish Terrier": "20 lbs",
            "Border Collie": "37 lbs",
            "Toy Poodle": "7 lbs"
        }
        return f"An average {breed} weighs {weights.get(breed, '50 lbs')}"

    @classmethod
    def get_actions(cls) -> Dict[str, Callable]:
        return {
            "calculate": cls.calculate,
            "average_dog_weight": cls.average_dog_weight
        }


class Agent:
    PROMPT = """
You run in a loop of Thought, Action, <PAUSE>, Observation.
At the end of the loop you output an Answer
Use Thought to describe your thoughts about the question you have been asked.
Use Action to run one of the actions available to you - then return PAUSE.
Observation will be the result of running those actions.

Your available actions are:

calculate:
e.g. calculate: 4 * 7 / 3
Runs a calculation and returns the number - uses Python so be sure to use floating point syntax if necessary

average_dog_weight:
e.g. average_dog_weight: Collie
returns average weight of a dog when given the breed

If available, always call a tool to inform your decisions, never use your parametric knowledge when a tool can be called. 

When you have decided that you need to call a tool, output <PAUSE> and stop thereafter! 

Example session:

Question: How much does a Bulldog weigh?
Thought: I should look the dogs weight using average_dog_weight
Action: average_dog_weight: Bulldog
<PAUSE>
----- execution stops here -----
You will be called again with this:

Observation: A Bulldog weights 51 lbs

You then output:

Answer: A bulldog weights 51 lbs
""".strip()

    def __init__(self, system: str = PROMPT):
        self.system = [{"text": system}] if system else []
        self.messages = []
        self.bedrock_client = BedrockClient().client
        self.action_handler = ActionHandler()
        self.action_re = re.compile(r"^Action: (\w+): (.*)$")

    def __call__(self, message: str) -> str:
        next_prompt = message
        for _ in range(5):  # Max 5 iterations
            self._add_user_message(next_prompt)
            result = self._execute()
            self._add_assistant_message(result)

            action_match = self._extract_action(result)
            if not action_match:
                return result

            action, action_input = action_match
            observation = self._handle_action(action, action_input)
            next_prompt = f"Observation: {observation}"

        return "Maximum iterations reached without final answer."

    def _add_user_message(self, message: str) -> None:
        self.messages.append({"role": "user", "content": [{"text": message}]})

    def _add_assistant_message(self, message: str) -> None:
        self.messages.append({"role": "assistant", "content": [{"text": message}]})

    def _extract_action(self, text: str) -> Optional[Tuple[str, str]]:
        actions = [self.action_re.match(a) for a in text.split("\n") if self.action_re.match(a)]
        return actions[0].groups() if actions else None

    def _handle_action(self, action: str, action_input: str) -> str:
        actions = self.action_handler.get_actions()
        if action not in actions:
            raise ValueError(f"Unknown action: {action}")
        return actions[action](action_input)

    def _execute(self) -> str:
        inference_config = {
            "temperature": 0.0,
            "stopSequences": ["<PAUSE>"],
        }
        additional_model_fields = {"top_k": 200}

        response = self.bedrock_client.converse(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            messages=self.messages,
            system=self.system,
            inferenceConfig=inference_config,
            additionalModelRequestFields=additional_model_fields,
        )
        return response["output"]["message"]["content"][0]["text"]

agent=Agent()
print(agent("How much does a Bulldog weigh?"))