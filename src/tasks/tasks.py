from crewai import Task


class InstructorTasks:
    def __init__(self, agent):
        self.agent = agent
        
    def quiz(self, tools, user_id, context, level, category, callback):
        return Task(
            description=f"""Create a single, new quiz (incremental quiz_id) for the user user_id={user_id}, in the 
                        category {category}, involving a grammar or vocabulary problem, with difficulty level 
                        {level}, where 1 is basic and 5 is difficult ("fluent"), Search web for
                        contextualize the quiz with the category {category} and formulate a good quiz for the choosen
                        dificulty level {level}.
                        use *word* instead of "word" to emphasize words (Markdown notation).
                        
                        ## Don't forget to check that the correct answer is not explicitly given in the question 
                        due to some error.
        
                        Do not repeat questions from the history: {context}. 
                        This tool should only be executed ONCE.""",
            expected_output="""A string in JSON format as the return from the 'quiz' tool (json_output). 
                        DO NOT ADD ANYTHING ELSE, NO COMMENTS OR MODIFY THE JSON OUTPUT. 
                        THE OUTPUT SHOULD be purely a JSON {}.
                        Do not try to 'reuse' the function. """,
            tools=tools,
            agent=self.agent,
            context=[],
            callback=callback,
            human_input=False
        )
        
    def dar_feedback(self, tools, user_id, context, callback):
        return Task(
            description=f"""Provide feedback to the student in the Telegram chat regarding 
                        the responses and performance in the activity: {context}.""",
            expected_output="""Give constructive feedback, indicating if the answer was correct ('user_alt' = 'answer') and if it was incorrect, explain why. 
                            If referencing the selected or correct alternative, use the content from the field. 
                            SEND ONLY THE FEEDBACK ONCE, NOTHING ELSE.""", #Use notação markdown e emojis para engajar
            tools=tools,
            agent=self.agent,
            context=[],
            callback=callback,
            human_input=False
        )
        
    def conversation(self, tools, user_id, context, callback):
        return Task(
            description=f"""Conduct a conversation activity with the student user_id={user_id}. Always maintain the
                        coherence of the subject with the context: {context}. When starting the conversation (empty context), 
                        send a welcoming message and engage the student to immediately finish the task, otherwise, the new 
                        message generated should directly refer only to the last item of the context. 
                        Pay attention to the student's needs and questions, providing corrections and tips on pronunciation, 
                        vocabulary, and grammar when relevant.""",
            expected_output="""a single round of conversation (interaction) with the student, returning a string with the message.
                            SEND ONLY ONCE, USE PLAIN TEXT.""", #Use notação markdown e emojis para engajar
            tools=tools,
            agent=self.agent,
            callback=callback,
            human_input=False
        )

class AssistantTasks:
    def __init__(self, agent):
        self.agent = agent  
              
    def conversation_assistant(self, tools, user_id, context, callback):
        return Task(
            description=f"""Assist the main instructor during the conversation activity with the student user_id={user_id}. 
                        You job is revise the instructor response in order to guarantee an outstanding interaction. 
                        Look at the lastest Instructor response in the context to get the topic: {context}. You can if need search the
                        internet, for a single query. Do not try call Action 'None'.""",
            expected_output="""A string with the revised message. SEND ONLY ONE, USE PLAIN TEXT.""", #Use notação markdown e emojis para engajar
            tools=tools,
            agent=self.agent,
            callback=callback,
            human_input=False
        )
