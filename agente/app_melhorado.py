import streamlit as st
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.document_loaders import PyPDFLoader, UnstructuredExcelLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from dotenv import load_dotenv
import os
from pathlib import Path
import xml.etree.ElementTree as ET


load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("""
    ⚠️ **OPENAI_API_KEY não encontrada!**
    
    **Para usar este agente, você precisa:**
    1. Criar um arquivo `.env` na pasta `agente/`
    2. Adicionar sua chave: `OPENAI_API_KEY=sua_chave_aqui`
    3. Obter sua chave em: https://platform.openai.com/api-keys
    
    """)
    st.stop()


BASE_DIR = Path(__file__).parent
PDF_PATH = BASE_DIR / "SCR_InstrucoesDePreenchimento_Doc3040.pdf"
XLS_PATH = BASE_DIR / "SCR3040_Leiaute.xls"
XML_PATH = BASE_DIR / "simulacao_3040.xml"
VECTORSTORE_PATH = BASE_DIR / "vectorstore"

st.set_page_config(
    page_title="Agente SCR 3040",
    page_icon="📘",
    layout="wide"
)


if "messages" not in st.session_state:
    st.session_state.messages = []
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )

@st.cache_resource
def carregar_vectorstore():
    """Carrega ou cria o vectorstore com cache"""
    import shutil
    
    # Verifica se o cache existe e está completo
    index_faiss = VECTORSTORE_PATH / "index.faiss"
    index_pkl = VECTORSTORE_PATH / "index.pkl"
    
    try:
        # Verifica se ambos os arquivos necessários existem
        if VECTORSTORE_PATH.exists() and index_faiss.exists() and index_pkl.exists():
            embeddings = OpenAIEmbeddings()
            vectorstore = FAISS.load_local(
                str(VECTORSTORE_PATH),
                embeddings,
                allow_dangerous_deserialization=True
            )
            st.success("✅ Vectorstore carregado do cache!")
            return vectorstore
        else:
            # Cache incompleto, remove e recria
            if VECTORSTORE_PATH.exists():
                shutil.rmtree(VECTORSTORE_PATH)
            st.info("ℹ️ Cache não encontrado ou incompleto. Criando novo vectorstore...")
    except Exception as e:
        # Erro ao carregar, remove cache corrompido e recria
        st.warning(f"⚠️ Erro ao carregar cache: {str(e)[:100]}. Recriando vectorstore...")
        try:
            if VECTORSTORE_PATH.exists():
                shutil.rmtree(VECTORSTORE_PATH)
        except:
            pass
    

    with st.spinner("📚 Carregando e processando documentos..."):
    
        if not PDF_PATH.exists():
            st.error(f"❌ Arquivo PDF não encontrado: {PDF_PATH}")
            st.stop()
        
        loader_pdf = PyPDFLoader(str(PDF_PATH))
        docs_pdf = loader_pdf.load()
        
 
        if not XLS_PATH.exists():
            st.error(f"❌ Arquivo XLS não encontrado: {XLS_PATH}")
            st.stop()
        
        loader_xls = UnstructuredExcelLoader(str(XLS_PATH))
        docs_xls = loader_xls.load()
        
        # Carrega XML
        if not XML_PATH.exists():
            st.error(f"❌ Arquivo XML não encontrado: {XML_PATH}")
            st.stop()
        
        # Carrega XML e extrai informações sobre tags e atributos
        try:
            tree = ET.parse(str(XML_PATH))
            root = tree.getroot()
            
            # Extrai informações sobre a estrutura XML
            xml_content = []
            xml_content.append(f"Estrutura do XML SCR 3040 - Exemplo de preenchimento\n")
            xml_content.append(f"Tag raiz: {root.tag}\n")
            xml_content.append(f"Atributos da tag raiz: {root.attrib}\n\n")
            
            # Processa elementos e seus atributos
            def processar_elemento(elem, nivel=0):
                indent = "  " * nivel
                xml_content.append(f"{indent}Tag: <{elem.tag}>")
                if elem.attrib:
                    xml_content.append(f"{indent}Atributos: {elem.attrib}")
                if elem.text and elem.text.strip():
                    xml_content.append(f"{indent}Conteúdo: {elem.text.strip()}")
                xml_content.append("")
                for child in elem:
                    processar_elemento(child, nivel + 1)
            
            processar_elemento(root)
            
            # Cria documento do XML
            xml_text = "\n".join(xml_content)
            docs_xml = [Document(
                page_content=xml_text,
                metadata={"source": "XML", "type": "exemplo_preenchimento"}
            )]
        except Exception as e:
            st.warning(f"⚠️ Erro ao processar XML: {e}. Tentando carregar como texto...")
            # Fallback: carrega como texto simples
            with open(XML_PATH, 'r', encoding='ISO-8859-1') as f:
                xml_text = f.read()
            docs_xml = [Document(
                page_content=f"Exemplo de XML SCR 3040:\n\n{xml_text}",
                metadata={"source": "XML", "type": "exemplo_preenchimento"}
            )]
        
        # Junta todos os documentos
        docs = docs_pdf + docs_xls + docs_xml
        
        # Adiciona metadados aos documentos
        for i, doc in enumerate(docs):
            if i < len(docs_pdf):
                doc.metadata["source"] = "PDF"
            elif i < len(docs_pdf) + len(docs_xls):
                doc.metadata["source"] = "XLS"
            else:
                doc.metadata["source"] = "XML"
            doc.metadata["doc_id"] = i
        
    
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        texts = text_splitter.split_documents(docs)
 
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(texts, embeddings)
        
        try:
            vectorstore.save_local(str(VECTORSTORE_PATH))
        except Exception as e:
            st.warning(f"⚠️ Não foi possível salvar cache: {e}")
        
        return vectorstore

@st.cache_resource
def criar_agente(_vectorstore, _memory):
    """Cria o agente RAG com configurações otimizadas"""
    
    # Prompt template melhorado
    template = """Você é um assistente especializado em documentos do Banco Central do Brasil, 
especificamente no documento SCR 3040. Sua função é ajudar usuários a entender e preencher 
corretamente este documento.

Use APENAS as informações fornecidas no contexto abaixo para responder. Se a informação 
não estiver no contexto, seja honesto e diga que não tem essa informação nos documentos.

Contexto:
{context}

Histórico da conversa:
{chat_history}

Pergunta: {question}

Resposta detalhada e precisa:"""
    
    PROMPT = PromptTemplate(
        template=template,
        input_variables=["context", "question", "chat_history"]
    )
    
   
    retriever = _vectorstore.as_retriever(
        search_type="mmr",  
        search_kwargs={
            "k": 5,  #
            "fetch_k": 10,  
            "lambda_mult": 0.7  
        }
    )
    
    
    llm = ChatOpenAI(
        model_name="gpt-4o-mini", 
        temperature=0.1,  
        max_tokens=2000
    )
    
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=_memory,
        combine_docs_chain_kwargs={"prompt": PROMPT},
        return_source_documents=True,
        verbose=False
    )
    
    return qa_chain

# 🌐 Interface
st.title("📘 Agente Inteligente do Documento SCR 3040")
st.markdown("**Assistente especializado** em ajudar com o preenchimento e estrutura do documento SCR 3040 do Banco Central.")

with st.sidebar:
    st.header("⚙️ Configurações")
  
    if st.button("🗑️ Limpar Histórico"):
        st.session_state.messages = []
        st.session_state.memory.clear()
        st.rerun()
    
    if st.button("🔄 Recriar Vectorstore"):
        import shutil
        if VECTORSTORE_PATH.exists():
            shutil.rmtree(VECTORSTORE_PATH)
        st.cache_resource.clear()
        st.success("✅ Vectorstore será recriado na próxima carga!")
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Informações")
    st.info("""
    **Modelo:** GPT-4o-mini  
    **Técnica:** RAG (Retrieval Augmented Generation)  
    **Vectorstore:** FAISS com MMR  
    **Cache:** Ativado
    """)
    
 
    if st.session_state.messages:
        st.metric("💬 Mensagens", len(st.session_state.messages))


try:
    vectorstore = carregar_vectorstore()
except Exception as e:
    st.error(f"❌ Erro ao carregar documentos: {e}")
    st.stop()


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if pergunta := st.chat_input("✍️ Faça sua pergunta sobre o SCR 3040:"):
    st.session_state.messages.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)
    
    with st.chat_message("assistant"):
        with st.spinner("🤔 Analisando documentos e gerando resposta..."):
            try:
             
                agente = criar_agente(vectorstore, st.session_state.memory)
                
           
                resultado = agente.invoke({"question": pergunta})
                resposta = resultado["answer"]
                documentos_fonte = resultado.get("source_documents", [])
                
   
                st.markdown(resposta)
                
                try:
                    search = DuckDuckGoSearchRun()
                    resultado_web = search.run(f"SCR 3040 Banco Central {pergunta}")
                    
                    if resultado_web and len(resultado_web.strip()) > 0:
                        with st.expander("🌐 Informação complementar da internet"):
                            st.write(resultado_web)
                except Exception as e:
                    # Trata rate limit e outros erros silenciosamente
                    error_msg = str(e).lower()
                    if "ratelimit" in error_msg or "rate limit" in error_msg or "202" in str(e):
                        # Rate limit - não mostra erro, apenas não exibe a busca
                        pass
                    else:
                        # Outros erros - mostra apenas se for algo crítico
                        pass
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": resposta,
                    "sources": documentos_fonte
                })
                
            except Exception as e:
                erro_msg = f"❌ Erro ao processar pergunta: {str(e)}"
                st.error(erro_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": erro_msg
                })

st.markdown("---")
st.markdown("### 🔗 Links Úteis")
col1, col2 = st.columns(2)
with col1:
    st.markdown("🔗 [Manual SCR 3040 - Banco Central](https://www.bcb.gov.br/estabilidadefinanceira/scr)")
with col2:
    st.markdown("🔗 [Perguntas Frequentes SCR](https://www.bcb.gov.br/estabilidadefinanceira/perguntasfrequentes)")

