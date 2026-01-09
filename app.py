import streamlit as st
import os
import warnings
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from sap_tools import get_material_stock

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

load_dotenv()

st.set_page_config(page_title="SAP Stok Asistanı", page_icon="📦", layout="centered")

st.title("📦 SAP Stok Yönetim Asistanı")
st.caption("Gemini 2.5 Flash & SAP OData Entegrasyonu")

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("GOOGLE_API_KEY bulunamadı! Lütfen .env dosyanızı kontrol edin.")
    st.stop()

@st.cache_resource
def get_llm_agent():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=0,
        google_api_key=api_key
    )
    tools = [get_material_stock]
    return llm.bind_tools(tools)

llm_with_tools = get_llm_agent()


if "messages" not in st.session_state:
    # Sistem mesajını geçmişin başına ekliyoruz
    system_text = (
        "Sen uzman bir SAP Stok Asistanısın. "
        "Kullanıcıların sorduğu malzemelerin stok durumunu kontrol edersin. "
        "Gerekirse get_material_stock tool'unu kullanırsın. "
        "\n\n**ÖNEMLİ KURALLAR:**\n"
        "1. Eğer 'Kritik_Seviye_Mi' TRUE ise, yanıtında mutlaka 🚨 (kırmızı alarm) emojisi kullan ve uyar.\n"
        "2. Stok miktarını, birimini ve malzeme açıklamasını net belirt.\n"
        "3. Yanıtlarını Türkçe ve profesyonel tut."
    )
    st.session_state.messages = [SystemMessage(content=system_text)]


for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.write(msg.content)
    elif isinstance(msg, AIMessage) and msg.content:
        with st.chat_message("assistant"):
            st.write(msg.content)


if user_input := st.chat_input("SAP Malzeme No veya sorunuzu girin..."):
    
    st.session_state.messages.append(HumanMessage(content=user_input))
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        response = llm_with_tools.invoke(st.session_state.messages)
        
        if hasattr(response, 'tool_calls') and response.tool_calls:
            
            st.session_state.messages.append(response)
            
            with st.status("SAP sistemi sorgulanıyor...", expanded=True) as status:
                
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    
                    st.write(f"🔍 Aranan Malzeme: `{tool_args.get('material_id')}`")
                    
                    if tool_name == 'get_material_stock':
                        tool_result = get_material_stock.invoke(tool_args)
                        
                        st.session_state.messages.append(
                            ToolMessage(
                                content=str(tool_result),
                                tool_call_id=tool_call['id']
                            )
                        )
                        
                        if tool_result.get("Bulundu_Mu"):
                            status.update(label="Veri bulundu!", state="complete")
                        else:
                            status.update(label="Veri bulunamadı.", state="error")
            
            final_response = llm_with_tools.invoke(st.session_state.messages)
            message_placeholder.markdown(final_response.content)
            st.session_state.messages.append(final_response)
            
        else:
            message_placeholder.markdown(response.content)
            st.session_state.messages.append(response)

ornek_sorular = [
    " Örnek sorular:",
    "   • WHITESUGAR-23 stoğu kaç?",
    "   • MAT-001 kritik seviyede mi?",
    "   • ABC-999 için stok bilgisi"
]

with st.sidebar:
    st.header("Sistem Durumu")
    st.success("SAP Bağlantısı: Aktif 🟢")
    if st.button("Sohbeti Temizle"):
        st.session_state.messages = [SystemMessage(content=st.session_state.messages[0].content)]
        st.rerun()
    st.divider() # Araya bir çizgi çeker
    
    st.subheader("Örnek Sorular")

    st.markdown("""
    - WHITESUGAR-23 stoğu kaç?
    - MAT-001 kritik seviyede mi?
    - ABC-999 için stok bilgisi
    """)