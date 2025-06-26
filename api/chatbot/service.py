from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate

class ChatBotAI:
    def __init__(self, prompt):
        self.prompt = prompt

    async def chat(self):
        self.model = init_chat_model(
            model="gpt-4o-mini",
            stream_usage=True,
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", "Provide a clear, in-depth, and easy-to-understand answer to the following question"),
            ("human", "{user_input}")
        ])

        llm_chain = prompt | self.model
        complete_response = await llm_chain.ainvoke({"user_input": self.prompt})

        return complete_response
