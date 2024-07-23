import os
import streamlit as st
import mm_agent

def initialize_state():
    # No es necesario inicializar api_key ya que se maneja en el backend
    st.session_state['dm'] = None
    st.session_state['result'] = None
    st.session_state["newvalues"] = None

def process_form(form_number,article):
    def set_value():
        print("set value",st.session_state.url)
        st.session_state["newvalues"]["url"]=st.session_state.url
        del st.session_state.newvalues["next"]
        
    def set_file():
        st.session_state["newvalues"].update({"raw":st.session_state.input_file.getvalue(),
                                    "file_name":st.session_state.input_file.name})
        
        del st.session_state.newvalues["next"]
    
    def do_first_dialog():
        words_in_article = st.slider("Número de palabras en el acta", 100, 2000, 500)

        # Radio buttons modificado para eliminar la opción "internet"
        source_document = st.radio("Fuente de la transcripción:", ["Mi PC"])
        
        # Buttons and logic
        if st.button('OK'):
            st.session_state['newvalues']={'origin':"upload",
                                        "words":words_in_article,"next":True}
            st.rerun()
    
    if form_number==0:
        if "origin" in article: #if initial dialog happened
            if article["origin"]=="upload": # Solo se maneja la opción de subir archivo
                st.file_uploader('Selecciona los documentos',
                                type=['pdf','docx','html','txt'],
                                accept_multiple_files=False,
                                help="""
                                This is the source for the story you want written.
                                It can be a pdf, docx, html, or text file
                                """,
                                on_change=(set_file),
                                key="input_file"
                                )
        if not "origin" in article: #if this is initial dialog
            do_first_dialog()
    elif form_number==1:
        header = article["title"]
        st.title(header)
        
        # Instructions (if any)
        instruction_text = "Puede editar el acta o la crítica.\n Borre la crítica para utilizar el acta tal y como se muestra."
        if instruction_text:
            st.write(instruction_text)
            
        markdown_template=""
            
        markdown_template = """
# {title}

## Fecha: 
{date}

## Asistentes

{attendees_list}

## Resumen

{summary}

## Principales Puntos de la Reunión

{takeaways_section}

## Conclusiones

{conclusions_section}

## Próxima reunión

{next_meeting_section}

## Tareas

{tasks_table}
        """
        attendees_list = "\n".join([f"- **{attendee['name']} ({attendee['position']}): {attendee['role']}" for attendee in st.session_state.result["attendees"]])
        takeaways_list = "\n".join([f"{index + 1}. {item}" for index, item in enumerate(article["takeaways"])])
        next_meeting_list = "\n".join([f"{index + 1}. {item}" for index, item in enumerate(article["next_meeting"])])
        conclusions_list = "\n".join([f"{index + 1}. {item}" for index, item in enumerate(article["conclusions"])])  
        table_header = "| Responsable | Fecha | Descripción |\n|-----------------|---------------|----------------------------------------------|\n"
        table_rows = "\n".join([f"| {task['responsible']} | {task['date']} | {task['description']} |" for task in st.session_state.result["tasks"]])

        attendees_list = attendees_list.strip()
        table_rows = table_rows.strip()

        tasks_table = table_header + table_rows

        write_content = markdown_template.format(
            title=st.session_state.result["title"],
            date=st.session_state.result["date"],
            attendees_list=attendees_list.strip(),
            summary=st.session_state.result["summary"],
            takeaways_section=takeaways_list,
            conclusions_section=conclusions_list,
            next_meeting_section=next_meeting_list,
            tasks_table=tasks_table
        )

        print(write_content)
        
        initial_contents = [write_content,article["critique"]]  
        titles = ["Borrador del acta", "Comentarios al acta"] 
        
        text_boxes = []
        for content, title in zip(initial_contents, titles):
            st.subheader(title)
            text_input = st.text_area("", value=content, height=150 if titles.index(title) == 0 else 50)
            text_boxes.append(text_input)
        
        if "url" in article:
            link_text = "Click here to open source document in browser."
            link_url = article["url"]
            st.markdown(f"[{link_text}]({link_url})", unsafe_allow_html=True)

        if st.button('OK'):
            st.session_state["newvalues"]={"body":text_boxes[0],"critique":text_boxes[1],"button":"OK"}
        
def rerun():
    st.session_state['dm'] = None
    st.session_state['result']=None
    st.session_state["newvalues"]=None
            
if 'dm' not in st.session_state:
    st.session_state['dm'] = None
    
if 'newvalues' not in st.session_state:
    st.session_state['newvalues'] = None

st.title("Elaboración de actas de reunión")

if st.session_state['dm'] is None:
    st.session_state['dm'] = mm_agent.StateMachine()
    st.session_state["result"]=st.session_state['dm'].start()

if st.session_state["result"]:
    print("have result")
    if "quit" not in st.session_state['result']:
        if st.session_state["newvalues"] is None:
            process_form(st.session_state['result']["form"],st.session_state['result'])
        if st.session_state["newvalues"] and "next" in st.session_state.newvalues:
            process_form(st.session_state['result']["form"],st.session_state.newvalues)
        if st.session_state["newvalues"] and not "next" in st.session_state.newvalues:
            with st.spinner("Please wait... Bots at work"):
                st.session_state["result"]=st.session_state['dm'].resume(st.session_state["newvalues"])
            st.session_state["newvalues"]=None
            st.rerun()
    if "quit" in st.session_state["result"]:
        markdown_template=""
            
        markdown_template = """
# {title}

## Fecha: 
{date}

## Asistentes

{attendees_list}

## Resumen

{summary}

## Principales Puntos de la Reunión

{takeaways_section}

## Conclusiones

{conclusions_section}

## Próxima reunión

{next_meeting_section}

## Tareas

{tasks_table}
        """
        attendees_list = "\n".join([f"- **{attendee['name']} ({attendee['position']}): {attendee['role']}" for attendee in st.session_state.result["attendees"]])
        takeaways_list = "\n".join([f"{index + 1}. {item}" for index, item in enumerate(st.session_state.result["takeaways"])])
        next_meeting_list = "\n".join([f"{index + 1}. {item}" for index, item in enumerate(st.session_state.result["next_meeting"])])
        conclusions_list = "\n".join([f"{index + 1}. {item}" for index, item in enumerate(st.session_state.result["conclusions"])])
        table_header = "| Responsable | Fecha | Descripción |\n|-----------------|---------------|----------------------------------------------|\n"
        table_rows = "\n".join([f"| {task['responsible']} | {task['date']} | {task['description']} |" for task in st.session_state.result["tasks"]])

        attendees_list = attendees_list.strip()
        table_rows = table_rows.strip()

        tasks_table = table_header + table_rows

        write_content = markdown_template.format(
            title=st.session_state.result["title"],
            date=st.session_state.result["date"],
            attendees_list=attendees_list.strip(),
            summary=st.session_state.result["summary"],
            takeaways_section=takeaways_list,
            conclusions_section=conclusions_list,
            next_meeting_section=next_meeting_list,
            tasks_table=tasks_table
        )
        
        st.write(write_content)
        
        st.write("\n \n")
        
        st.button("Run with new document",key="rerun",on_click=rerun)
