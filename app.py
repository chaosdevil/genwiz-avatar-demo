import os
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from typing import Optional, Dict, List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents import AgentExecutor
from langchain.tools import Tool, tool
import smtplib, ssl
from dotenv import load_dotenv


load_dotenv()


app = FastAPI()


# genai start here
llm = AzureChatOpenAI(
    name="GenWiz",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"), 
    api_key=os.getenv("AZURE_OPENAI_KEY"),  
    api_version=os.getenv("AZURE_OPENAI_VERSION"),
    temperature=0.7,
    model='general-model'
)


@tool
def send_email(mail_message: str, sender_email: str, receiver_email: List[str]):
    """Useful when it is necessary to send an email to the employees in charge"""

    for email in receiver_email:
        message = port = 465  # For SSL
        smtp_server = "smtp.gmail.com"
        sender_email = sender_email  # Enter your address, should be gmail
        receiver_email = email  # Enter receiver address
        password = "spvl mrur psjk kstl"
        message = mail_message.encode("UTF-8")

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)
            print("Send email")

    return "Email has been sent"

tools = [
    send_email,
]

llm_with_tools = llm.bind_tools(tools=tools)

report = ""

system_prompt = """
You work for a manufacturing company in Thailand as a Thai **female** quality assurance engineer. 
Your task is to help identify any problems in the manufacturing line and report them to the user.
You are good at Thai language. You can quickly understand Thai language. And you are to support Thai language only.
You also have good memory, so you can reference conversation history from your memory.
You have capability of generating human-like responses and your responses are polite as well.

## Instructions
- Report the problem you found to the user.
- Detect the language used in the question.
- Classify the levels of damage.
- Estimate the time taken to solve the problem.
- Recommend a potential solution to the problem.
- To send an email to the employees in charge, do the following:
    - Ask for sender's name, work position and email address.
    - Ask for receiver's name and email address. Receiver can be multiple.
- If you don't find the answer, don't make up the answer. Do not make up the answer. Just say that you don't know and ask for further information.

## Knowledge
### Employees
ลำดับที่	รหัสพนักงาน	พนักงาน	หน่วยงาน	พฤษภาคม 2024																														
				1	2	3	4	5	6	7	8	9	10	11	12	13	14	15	16	17	18	19	20	21	22	23	24	25	26	27	28	29	30	31
1	DLG020143	นายสมหมาย สุขใจ	ช่างซ่อม	/	/	/			/	/	/						/	/	/					/	/		/					/	/	/
2	DLG020144	นายสมศรี สมาน	ช่างซ่อม	/	/	/			/	/	/						/	/	/					/	/		/					/	/	/
3	DLG020145	นายสมศักดิ์ รัชชา	ช่างซ่อม	/	/	/			/	/	/						/	/	/					/	/		/					/	/	/
4	DLG020146	นายรพีย์ พัฒน์	ช่างซ่อม	/	/	/			/	/	/						/	/	/					/	/		/					/	/	/
5	DLG020147	นายจณัตว์ สุวรรณวงศ์	ช่างซ่อม		/	/					/	/	/			/			/	/			/			/	/			/	/	/		
6	DLG020148	นางสาวสุดใจ ทดสอบ	ผู้ประสานงาน		/	/					/	/	/			/			/	/			/			/	/			/	/	/		
7	DLG020149	นางสาวกลม รักษา	ผู้ประสานงาน		/	/					/	/	/			/			/	/			/			/	/			/	/	/		
8	DLG020150	นางสาวไพลิน ขมิ้น	ผู้ประสานงาน		/	/					/	/	/			/			/	/			/			/	/			/	/	/		
9	DLG020151	นายกองทัพ มหาด	ผู้ตรวจสอบ	/	/				/	/			/			/	/	/					/	/	/							/	/	/
10	DLG020152	นายทดสอบ ระบบ	ผู้ตรวจสอบ	/	/				/	/			/			/	/	/					/	/	/							/	/	/


## Output
- Answer should be concise and targeted.
- Make answer as human-like as possible.
- If there are lists, use unordered lists.
"""

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            system_prompt,
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        MessagesPlaceholder(variable_name="problem"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_to_openai_tool_messages(
            x["intermediate_steps"]
        ),
        "chat_history": lambda x: x["chat_history"],
        "problem": lambda x: x["problem"],
    }
    | prompt
    | llm_with_tools
    | OpenAIToolsAgentOutputParser()
)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


class QueryRequest(BaseModel):
    query: Optional[str]
    enable_chat_history: Optional[bool]
    chat_history: Optional[List[Dict[str, str]]]


class ReportRequest(BaseModel):
    part_name: Optional[str] 
    line: Optional[str]
    problem: Optional[str]
    date: Optional[str]
    time: Optional[str]


@app.get(path="/", status_code=200)
async def start():
    return {"message": "Hello World"}

@app.post(path="/ultimate_v1/report_problem", status_code=200)
async def report_problem(request: ReportRequest):
    global report
    report = f"Part name: {request.part_name}\nLine: {request.line}\nProblem: {request.problem}\nDate: {request.date}\nTime: {request.time}"
    return {"message": {"response": report}}

@app.post(path="/ultimate_v1/chat", status_code=200)
async def chat(request: QueryRequest):

    # create chat history
    chat_history = []
    if request.enable_chat_history:
        for pair in request.chat_history:
            chat_history.extend([HumanMessage(content=pair["Human"]), AIMessage(content=pair["AI"])])
    
    # create query
    response = agent_executor.invoke({"input": request.query, "chat_history": chat_history, "problem": [report]})

    response["facialExpression"] = "smile"

    return response
