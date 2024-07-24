import os
import streamlit as st
import mm_agent
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import tempfile
import base64

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

{attendees_table}

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
        attendees_table = "| Nombre | Posición | Rol |\n|--------|----------|-----|\n"
        attendees_table += "\n".join([f"| {attendee['name']} | {attendee['position']} | {attendee['role']} |" for attendee in st.session_state.result["attendees"]])
        takeaways_list = "\n".join([f"{index + 1}. {item}" for index, item in enumerate(article["takeaways"])])
        next_meeting_list = "\n".join([f"{index + 1}. {item}" for index, item in enumerate(article["next_meeting"])])
        conclusions_list = "\n".join([f"{index + 1}. {item}" for index, item in enumerate(article["conclusions"])])  
        table_header = "| Responsable | Fecha | Descripción |\n|-----------------|---------------|----------------------------------------------|\n"
        table_rows = "\n".join([f"| {task['responsible']} | {task['date']} | {task['description']} |" for task in st.session_state.result["tasks"]])

        attendees_table = attendees_table.strip()
        table_rows = table_rows.strip()

        tasks_table = table_header + table_rows

        write_content = markdown_template.format(
            title=st.session_state.result["title"],
            date=st.session_state.result["date"],
            attendees_table=attendees_table,
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
    st.session_state['result'] = None
    st.session_state["newvalues"] = None

def generate_html_content(result):
    html_template = """
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }}
            h2 {{ color: #34495e; margin-top: 20px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            ul {{ padding-left: 20px; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <h2>Fecha:</h2>
        <p>{date}</p>
        <h2>Asistentes:</h2>
        {attendees_table}
        <h2>Resumen:</h2>
        <p>{summary}</p>
        <h2>Principales Puntos de la Reunión:</h2>
        <ol>
        {takeaways_section}
        </ol>
        <h2>Conclusiones:</h2>
        <ol>
        {conclusions_section}
        </ol>
        <h2>Próxima reunión:</h2>
        <ol>
        {next_meeting_section}
        </ol>
        <h2>Tareas:</h2>
        {tasks_table}
    </body>
    </html>
    """
    attendees_table = "<table><tr><th>Nombre</th><th>Posición</th><th>Rol</th></tr>"
    attendees_table += "".join([f"<tr><td>{attendee['name']}</td><td>{attendee['position']}</td><td>{attendee['role']}</td></tr>" for attendee in result["attendees"]])
    attendees_table += "</table>"
    takeaways_list = "".join([f"<li>{item}</li>" for item in result["takeaways"]])
    next_meeting_list = "".join([f"<li>{item}</li>" for item in result["next_meeting"]])
    conclusions_list = "".join([f"<li>{item}</li>" for item in result["conclusions"]])
    tasks_table = "<table><tr><th>Responsable</th><th>Fecha</th><th>Descripción</th></tr>"
    tasks_table += "".join([f"<tr><td>{task['responsible']}</td><td>{task['date']}</td><td>{task['description']}</td></tr>" for task in result["tasks"]])
    tasks_table += "</table>"

    return html_template.format(
        title=result["title"],
        date=result["date"],
        attendees_table=attendees_table,
        summary=result["summary"],
        takeaways_section=takeaways_list,
        conclusions_section=conclusions_list,
        next_meeting_section=next_meeting_list,
        tasks_table=tasks_table
    )

def html_to_pdf(html_content):
    font_config = FontConfiguration()
    html = HTML(string=html_content)
    css = CSS(string='''
        @page { size: A4; margin: 1cm }
    ''', font_config=font_config)
    
    # Use a temporary file for the PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        html.write_pdf(tmp_file.name, stylesheets=[css], font_config=font_config)
        return tmp_file.name

if 'dm' not in st.session_state:
    st.session_state['dm'] = None
    
if 'newvalues' not in st.session_state:
    st.session_state['newvalues'] = None

st.title("Elaboración de actas de reunión")

if st.session_state['dm'] is None:
    st.session_state['dm'] = mm_agent.StateMachine()
    st.session_state["result"] = st.session_state['dm'].start()

if st.session_state["result"]:
    print("have result")
    if "quit" not in st.session_state['result']:
        if st.session_state["newvalues"] is None:
            process_form(st.session_state['result']["form"], st.session_state['result'])
        if st.session_state["newvalues"] and "next" in st.session_state.newvalues:
            process_form(st.session_state['result']["form"], st.session_state.newvalues)
        if st.session_state["newvalues"] and "next" not in st.session_state.newvalues:
            with st.spinner("Please wait... Bots at work"):
                st.session_state["result"] = st.session_state['dm'].resume(st.session_state["newvalues"])
            st.session_state["newvalues"] = None
            st.rerun()
    if "quit" in st.session_state["result"]:
        html_content = generate_html_content(st.session_state.result)
        st.components.v1.html(html_content, height=600, scrolling=True)
        
        st.write("\n \n")
        
        # Generate PDF and provide download button
        pdf_path = html_to_pdf(html_content)
        with open(pdf_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
            b64 = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="acta_reunion.pdf">Descargar acta en PDF</a>'
            st.markdown(href, unsafe_allow_html=True)
        
        st.button("Run with new document", key="rerun", on_click=rerun)

        # Clean up the temporary PDF file
        os.unlink(pdf_path)