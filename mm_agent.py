from datetime import datetime
import json5 as json

from langgraph.graph import Graph

from langchain.adapters.openai import convert_openai_messages
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_cohere import ChatCohere

from dotenv import load_dotenv

load_dotenv()


#MODEL='gpt-4-turbo'
#MODEL='llama3-8b-8192'
#MODEL='llama3-70b-8192'
MODEL='command-r-plus'

class WriterAgent:

    def writer(self, the_text:str,word_count=500):
        
        sample_json = """
            {
            "title": Title of the meeting,
            "date": Date of the meeting,
            "attendees": List of dictionaries of the meeting attendees. The dictionaries must have the following key values: "name", "position" and "role". The "role" key refers to the attendee's function in the meeting. If any of the values of these keys is not clear or is not mentioned, it is given the value "none".
            "summary": "succinctly summarize the minutes of the meeting in 3 clear and coherent paragraphs. Separete paragraphs using newline characters.",
            "takeaways": List of the takeaways of the meeting minute,
            "conclusions": List of conclusions and actions to be taken,
            "next_meeting": List of the commitments made at the meeting. Be sure to go through the entire content of the meeting before giving your answer,
            "tasks": List of dictionaries for the commitments acquired in the meeting. The dictionaries must have the following key values "responsible", "date" and "description". In the key-value  "description", it is advisable to mention specifically what the person in charge is expected to do instead of indicating general actions. Be sure to include all the items in the next_mmeting list,
            "message": "message to the critique",
            }
            """

        prompt = [{
            "role": "system",
            "content":"As an expert in minute meeting creation, you are a chatbot designed to facilitate the process of "
                    "generating meeting minutes efficiently.\n" 
                    
                    "Please return nothing but a JSON in the following format:\n"
                    f"{sample_json}\n"
                    

                    "Respond in Spanish.\n" 

                    "Ensure that your responses are structured, concise, and provide a comprehensive overview of the meeting proceedings for"
                    "effective record-keeping and follow-up actions."

                    
        }, {
            "role": "user",
            "content": f"Today's date is {datetime.now().strftime('%d/%m/%Y')}\n."

                    f"{the_text}\n"
                    f""""Your task is to write up for me the minutes of the meeting described above, including all the points of the meeting.
                    The meeting minutes should be approximately {word_count} words and should be divided into paragraphs
                    using newline characters."""


        }]
        #print(f"prompt: {prompt}")
        
        lc_messages = convert_openai_messages(prompt)
        
        #print(f"lc_messages: {lc_messages}")
        optional_params = {
            "response_format": {"type": "json_object"}
        }

        #response = ChatOpenAI(model=MODEL, max_retries=1, temperature=.5,model_kwargs=optional_params).invoke(lc_messages).content
        #response = ChatGroq(model_name=MODEL, max_retries=1, temperature=.5,model_kwargs=optional_params).invoke(lc_messages).content
        response = ChatCohere(model=MODEL, max_retries=1, temperature=.5,model_kwargs=optional_params).invoke(lc_messages).content

        print (f"Response from Writer: {response}")
        cleaned_response = response.strip("`").strip("\n").strip("json").strip("")
        return json.loads(cleaned_response)

    def revise(self, article: dict):
        sample_revise_json = """
            {
            "title": Title of the meeting,
            "date": Date of the meeting,
            "attendees": List of dictionaries of the meeting attendees. The dictionaries must have the following key values: "name", "position" and "role". The "role" key refers to the attendee's function in the meeting. If any of the values of these keys is not clear or is not mentioned, it is given the value "none".
            "summary": "succinctly summarize the minutes of the meeting in 3 clear and coherent paragraphs. Separete paragraphs using newline characters.",
            "takeaways": List of the takeaways of the meeting minute,
            "conclusions": List of conclusions and actions to be taken,
            "next_meeting": List of the commitments made at the meeting. Be sure to go through the entire content of the meeting before giving your answer,
            "tasks": List of dictionaries for the commitments acquired in the meeting. The dictionaries must have the following key values "responsible", "date" and "description". In the key-value  "description", it is advisable to mention specifically what the person in charge is expected to do instead of indicating general actions. Be sure to include all the items in the next_mmeting list,
            "message": "message to the critique",
            }
            """
        prompt = [{
            "role": "system",
            "content": "You are an expert meeting minutes creator in Spanish. Your sole purpose is to edit well-written minutes on a  "
                       "topic based on given critique\n "
                       "Respond in Spanish language"
        }, {
            "role": "user",
            "content": f"{str(article)}\n"
                        f"Your task is to edit the meeting minutes based on the critique given.\n "
                        f"Please return json format of the 'dictionaries' and a new 'message' field"
                        f"to the critique that explain your changes or why you didn't change anything.\n"
                        f"please return nothing but a JSON in the following format:\n"
                        f"{sample_revise_json}\n "

        }]

        lc_messages = convert_openai_messages(prompt)
        optional_params = {
            "response_format": {"type": "json_object"}
        }

        #response = ChatOpenAI(model=MODEL, max_retries=1, temperature=.5,model_kwargs=optional_params).invoke(lc_messages).content
        #response = ChatGroq(model_name=MODEL, max_retries=1, temperature=.5,model_kwargs=optional_params).invoke(lc_messages).content
        response = ChatCohere(model=MODEL, max_retries=1, temperature=.5,model_kwargs=optional_params).invoke(lc_messages).content
        cleaned_response = response.strip("`").strip("\n").strip("json").strip("")
        response = json.loads(cleaned_response)
        #print(f"For article: {article['title']}")
        print(f"Writer Revision Message: {response['message']}\n")
        return response

    def run(self, article: dict):
        print("writer working...",article.keys())
        critique = article.get("critique")
        if critique is not None:
            article.update(self.revise(article))
        else:
            article.update(self.writer( article["source"],word_count=article['words']))
        return article


class CritiqueAgent:

    def critique(self, article: dict):
        short_article=article.copy()
        del short_article['source'] #to save tokens
        prompt = [{
            "role": "system",
            "content": "You are critical of meeting minutes. Its sole purpose is to provide brief feedback on an "
                    "meeting minutes so the writer knows what to fix.\n "
                    "Respond in Spanish"
        }, {
            "role": "user",
            "content": f"Today's date is {datetime.now().strftime('%d/%m/%Y')}\n."
                    f"{str(short_article)}\n"
                    f"Your task is to provide  feedback on the meeting minutes only if necessary.\n"
                    f"Be sure that names are given for split votes and for debate."
                    f"The maker of each motion should be named."
                    f"if you think the meeting minutes is good, please return only the word 'None' without the surrounding hash marks.\n"
                    f"do NOT return any text except the word 'None' without surrounding hash marks if no further work is needed onthe article."
                    f"if you noticed the field 'message' in the meeting minutes, it means the writer has revised the meeting minutes"
                    f"based on your previous critique. The writer may have explained in message why some of your"
                    f"critique could not be accomodated. For example, something you asked for is not available information."
                    f"you can provide feedback on the revised meeting minutes or "
                    f"return only the word 'None' without surrounding hash mark if you think the article is good."
        }] 

        lc_messages = convert_openai_messages(prompt)
        response = ChatOpenAI(model="gpt-4",temperature=1.0, max_retries=1).invoke(lc_messages).content
        #response = ChatGroq(model_name=MODEL, max_retries=1, temperature=1.0).invoke(lc_messages).content
        #response = ChatCohere(model=MODEL, max_retries=1, temperature=1.0).invoke(lc_messages).content


        if response == 'None':
            return {'critique': None}
        else:
            print(f"For article: {article['title']}")
            print(f"Feedback: {response}\n")
            return {'critique': response, 'message': None}

    def run(self, article: dict):
        print("critiquer working...",article.keys())
        article.update(self.critique(article))
        article["form"]=1
        if "message" in article:
            print('message',article['message'])
        return article


class InputAgent:
    def run(self,article:dict):
        from mytools import extract_text, load_text_from_path, load_text_from_url
        
        print ("input agent running...")
        print(article.keys())
        if "url" in article:
            the_text=load_text_from_url(article["url"])
            
        else:
            if "raw" in article: #if already read
                the_text=extract_text(content=article['raw'],content_type=article["file_name"].split('.')[-1])
                del article["raw"]
            else:
                the_text=load_text_from_path(article['file_name'])
        article["source"]=the_text
        return article
            
class OutputAgent:
    def run(self,article:dict):
        print(f"Title: {article['title']}\nSummary: {article['summary']}\nBody:{article['body']}")
        return article
      
class HumanReviewAgent:
    def run(self,article:dict):
        print("human review agent running",article.keys())
        if article["button"]=='OK':
            if not article["critique"]:
                article["critique"]=None
                article["quit"]="yes"
        else:
            assert False,"Canceled by editor"
        #print("from user:",article["body"],"\n","from dialog:",result["text1"])
        return article
    
class StartAgent:
    name='start'
    def run(self,dummy):
        print("start agent working")
        return {"form":0,"name":self.name}
          
            
        
class StateMachine:
    def __init__(self,api_key=None):
        import os
        from langgraph.checkpoint.sqlite import SqliteSaver
        import sqlite3
        
        def from_conn_stringx(cls, conn_string: str,) -> "SqliteSaver":
            return SqliteSaver(conn=sqlite3.connect(conn_string, check_same_thread=False))
        SqliteSaver.from_conn_stringx=classmethod(from_conn_stringx)

        if api_key:
            os.environ['OPENAI_API_KEY']=api_key
        else:
            from dotenv import load_dotenv
            load_dotenv()
        self.memory = SqliteSaver.from_conn_stringx(":memory:")

        start_agent=StartAgent()
        input_agent=InputAgent()
        writer_agent = WriterAgent()
        critique_agent = CritiqueAgent()
        output_agent=OutputAgent()
        human_review=HumanReviewAgent()

        workflow = Graph()

        workflow.add_node(start_agent.name,start_agent.run)
        workflow.add_node("input",input_agent.run)
        workflow.add_node("write", writer_agent.run)
        workflow.add_node("critique", critique_agent.run)
        workflow.add_node("output",output_agent.run)
        workflow.add_node("human_review",human_review.run)

        #workflow.add_edge(start_agent.name,"input")
        workflow.add_edge("input","write")

        workflow.add_edge('write', 'critique')
        workflow.add_edge('critique','human_review')
        workflow.add_edge(start_agent.name,"input")
        workflow.add_conditional_edges(start_key='human_review',
                                    condition=lambda x: "accept" if x['critique'] is None else "revise",
                                    conditional_edge_mapping={"accept": "output", "revise": "write"})
                                    
        
        # set up start and end nodes
        workflow.set_entry_point(start_agent.name)
        workflow.set_finish_point("output")
        
        self.thread={"configurable": {"thread_id": "2"}}
        self.chain=workflow.compile(checkpointer=self.memory,interrupt_after=[start_agent.name,"critique"])
    def start(self):
        result=self.chain.invoke("",self.thread)
        print("*",self.chain.get_state(self.thread),"*")
        print("r",result)
        if result is None:
            values=self.chain.get_state(self.thread).values
            last_state=next(iter(values))
            return values[last_state]
        return result
        
    def resume(self,new_values:dict):
        values=self.chain.get_state(self.thread).values
        #last_state=self.chain.get_state(self.thread).next[0].split(':')[0]
        last_state=next(iter(values))
        #print(self.chain.get_state(self.thread))
        values[last_state].update(new_values)
        self.chain.update_state(self.thread,values[last_state])
        result=self.chain.invoke(None,self.thread,output_keys=last_state)
        #print("r",result)
        if result is None:
            values=self.chain.get_state(self.thread).values
            last_state=next(iter(values))
            return self.chain.get_state(self.thread).values[last_state]
        return result       
      

if __name__ == '__main__': #test code
    
    from mm_tkinter import process_form

       
    sm=StateMachine()
    result =sm.start()
    while "quit" not in result:
        new_values=process_form(result["form"],result)
        result=sm.resume (new_values)
    