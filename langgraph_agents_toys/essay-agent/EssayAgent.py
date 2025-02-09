# essay_agent.py
from dotenv import load_dotenv
import boto3
from botocore.config import Config
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from langgraph.checkpoint.memory import MemorySaver
from tavily import TavilyClient
import os
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_aws import ChatBedrockConverse
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
import json
import streamlit as st
from StepParser import StepParser

load_dotenv("../.env")

class Queries(BaseModel):
    queries: List[str] = Field(description="List of research queries")

class AgentState(TypedDict):
    task: str
    plan: str
    draft: str
    critique: str
    content: List[str]
    revision_number: int
    max_revisions: int

class EssayAgent:
    def __init__(self, model_name: str = "anthropic.claude-3-haiku-20240307-v1:0"):
        self.tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
        self.bedrock_client = self._create_bedrock_client()
        self.memory = MemorySaver()
        self.stepParser=StepParser()
        self.graph = self._build_graph()
        self.model = ChatBedrockConverse(
            client=self.bedrock_client,
            model=model_name,
            temperature=0,
            max_tokens=None,
        )
        
        self.PLAN_PROMPT = """You are an expert writer tasked with writing a high level outline of an essay. \
        Write such an outline for the user provided topic. Give an outline of the essay along with any relevant notes \
        or instructions for the sections."""

        self.WRITER_PROMPT = """You are an essay assistant tasked with writing excellent 5-paragraph essays.\
        Generate the best essay possible for the user's request and the initial outline. \
        If the user provides critique, respond with a revised version of your previous attempts. \
        Utilize all the information below as needed: 
        ------
        <content>
        {content}
        </content>"""

        self.REFLECTION_PROMPT = """You are a teacher grading an essay submission. \
        Generate critique and recommendations for the user's submission. \
        Provide detailed recommendations, including requests for length, depth, style, etc."""

        self.RESEARCH_PLAN_PROMPT = """You are a researcher charged with providing information that can \
        be used when writing the following essay. Generate a list of search queries that will gather \
        any relevant information. Only generate 3 queries max."""

        self.RESEARCH_CRITIQUE_PROMPT = """You are a researcher charged with providing information that can \
        be used when making any requested revisions (as outlined below). \
        Generate a list of search queries that will gather any relevant information. Only generate 3 queries max."""

    def _create_bedrock_client(self):
        config = Config(
            connect_timeout=120,
            read_timeout=120,
            retries={"max_attempts": 0}
        )
        return boto3.client(
            "bedrock-runtime",
            region_name='us-west-2',
            config=config,
        )

    def _build_graph(self):
        builder = StateGraph(AgentState)
        
        # Add nodes
        builder.add_node("planner", self.plan_node)
        builder.add_node("generate", self.generation_node)
        builder.add_node("reflect", self.reflection_node)
        builder.add_node("research_plan", self.research_plan_node)
        builder.add_node("research_critique", self.research_critique_node)
        
        # Set up edges
        builder.set_entry_point("planner")
        builder.add_conditional_edges(
            "generate", self.should_continue, {END: END, "reflect": "reflect"}
        )
        builder.add_edge("planner", "research_plan")
        builder.add_edge("research_plan", "generate")
        builder.add_edge("reflect", "research_critique")
        builder.add_edge("research_critique", "generate")
        
        return builder.compile(checkpointer=self.memory)

    def plan_node(self, state: AgentState):
        messages = [SystemMessage(content=self.PLAN_PROMPT), 
                   HumanMessage(content=state["task"])]
        response = self.model.invoke(messages)
        return {"plan": response.content}

    def research_plan_node(self,state: AgentState):

        # Set up the Pydantic output parser
        parser = PydanticOutputParser(pydantic_object=Queries)

        # Create a prompt template with format instructions
        prompt = PromptTemplate(
            template="Generate research queries based on the given task.\n{format_instructions}\nTask: {task}\n",
            input_variables=["task"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        # Use the model with the new prompt and parser
        queries_output = self.model.invoke(prompt.format_prompt(task=state["task"]))

        # Extract the content from the AIMessage
        queries_text = queries_output.content

        # Extract the JSON string from the content
        json_start = queries_text.find("{")
        json_end = queries_text.rfind("}") + 1
        json_str = queries_text[json_start:json_end]

        # Parse the JSON string
        queries_dict = json.loads(json_str)

        # Create a Queries object from the parsed JSON
        parsed_queries = Queries(**queries_dict)

        content = []
        for q in parsed_queries.queries:
            response = self.tavily.search(query=q, max_results=2)
            for r in response["results"]:
                content.append(r["content"])
        return {"content": content}

    def generation_node(self,state: AgentState):
        content = "\n\n".join(state["content"] or [])
        user_message = HumanMessage(
            content=f"{state['task']}\n\nHere is my plan:\n\n{state['plan']}"
        )
        messages = [
            SystemMessage(content=self.WRITER_PROMPT.format(content=content)),
            user_message,
        ]
        response = self.model.invoke(messages)
        return {
            "draft": response.content,
            "revision_number": state.get("revision_number", 1) + 1,
        }

    def reflection_node(self,state: AgentState):
        messages = [
            SystemMessage(content=self.REFLECTION_PROMPT),
            HumanMessage(content=state["draft"]),
        ]
        response = self.model.invoke(messages)
        return {"critique": response.content}


    def research_critique_node(self,state: AgentState):
        # Set up the Pydantic output parser
        parser = PydanticOutputParser(pydantic_object=Queries)

        # Create a prompt template with format instructions
        prompt = PromptTemplate(
            template="Generate research queries based on the given critique.\n{format_instructions}\nCritique: {critique}\n",
            input_variables=["critique"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        # Use the model with the new prompt and parser
        queries_output = self.model.invoke(prompt.format_prompt(critique=state["critique"]))

        # Extract the content from the AIMessage
        queries_text = queries_output.content

        # Extract the JSON string from the content
        json_start = queries_text.find("{")
        json_end = queries_text.rfind("}") + 1
        json_str = queries_text[json_start:json_end]

        # Parse the JSON string
        queries_dict = json.loads(json_str)

        # Create a Queries object from the parsed JSON
        parsed_queries = Queries(**queries_dict)

        content = state["content"] or []
        for q in parsed_queries.queries:
            response = self.tavily.search(query=q, max_results=2)
            for r in response["results"]:
                content.append(r["content"])
        return {"content": content}

    def should_continue(self, state):
        if state["revision_number"] > state["max_revisions"]:
            return END
        return "reflect"
    def generate_essay(self, task: str, max_revisions: int = 2, thread_id: str = "default"):
        thread = {"configurable": {"thread_id": thread_id}}
        inputs = {
            "task": task,
            "max_revisions": max_revisions,
            "revision_number": 1
        }
        for step in self.graph.stream(inputs, thread):
            self.stepParser.parse_and_display(step)
            
        
        
    
