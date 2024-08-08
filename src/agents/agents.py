import os
from crewai import Agent
from langchain_groq import ChatGroq



class Agents():
    def __init__(self, tools):
        self.llm = ChatGroq(temperature=0, api_key=os.getenv("GROQ_API_KEY"), model="llama3-70b-8192")
        self.allow_delegation = False
        self.verbose = False
        self.tools = tools
        
    def instructor_agent(self) -> Agent:
        return Agent(
            role="English Instructor",
            goal="""
                Understand student inputs, provide appropriate responses, guide didactic activities, 
                and facilitate conversation classes. Determine when to respond to the student in English 
                 in Portuguese.""",
            backstory="""
                The English Instructor is a dedicated agent for teaching the English language. 
                They have extensive knowledge of grammar, vocabulary, and conversational practices. 
                Their goal is to help students improve their communication skills in English by 
                offering immediate feedback and personalized guidance.""",
            expected_output="""
                The English Instructor is expected to provide accurate and helpful answers to student questions, 
                guide them through didactic activities, and practice real-time conversation, 
                while keeping a record of each student's progress.""",
            verbose=self.verbose,
            allow_delegation=self.allow_delegation,
            tools=self.tools,
            max_iter=10,
            llm=self.llm, 
        )
        
    def assistant_agent(self) -> Agent:
        return Agent(
            role="Conversation Assistant",
            goal="""
                Assist and review the Instructor conversation responses in order to improve the interation.""",
            backstory="""
                The Conversation Assistant is a dedicated agent for conversational sessions. 
                They have extensive knowledge for searching, review and relationship skills. 
                Their goal is to help the instructor improve their communication 
                in English by offering immediate quality review service.""",
            expected_output="""
                Aaccurate and helpful review string of the instructor response in a real-time conversation session.""",
            verbose=self.verbose,
            allow_delegation=self.allow_delegation,
            tools=self.tools,
            llm=self.llm, 
        )

    

    