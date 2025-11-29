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
XLS_CRITICAS_PATH = BASE_DIR / "SCR3040_Criticas.xls"
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
# Memórias separadas para cada modelo (para comparação)
if "memories_modelos" not in st.session_state:
    st.session_state.memories_modelos = {}

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
        
        # Carrega arquivo XLS de Críticas
        if XLS_CRITICAS_PATH.exists():
            loader_xls_criticas = UnstructuredExcelLoader(str(XLS_CRITICAS_PATH))
            docs_xls_criticas = loader_xls_criticas.load()
        else:
            st.warning(f"⚠️ Arquivo de críticas não encontrado: {XLS_CRITICAS_PATH}. Continuando sem ele...")
            docs_xls_criticas = []
        
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
        docs = docs_pdf + docs_xls + docs_xls_criticas + docs_xml
        
        # Adiciona metadados aos documentos
        for i, doc in enumerate(docs):
            if i < len(docs_pdf):
                doc.metadata["source"] = "PDF"
            elif i < len(docs_pdf) + len(docs_xls):
                doc.metadata["source"] = "XLS_Leiaute"
            elif i < len(docs_pdf) + len(docs_xls) + len(docs_xls_criticas):
                doc.metadata["source"] = "XLS_Criticas"
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

# Modelos disponíveis
MODELOS_DISPONIVEIS = {
    "GPT-4o-mini": {
        "nome": "gpt-4o-mini",
        "descricao": "Modelo mais rápido e econômico",
        "custo": "Baixo"
    },
    "GPT-3.5-turbo": {
        "nome": "gpt-3.5-turbo",
        "descricao": "Modelo balanceado (velocidade/custo)",
        "custo": "Muito Baixo"
    },
    "GPT-4o": {
        "nome": "gpt-4o",
        "descricao": "Modelo mais avançado e preciso",
        "custo": "Alto"
    },
    "GPT-4-turbo": {
        "nome": "gpt-4-turbo",
        "descricao": "Modelo GPT-4 otimizado",
        "custo": "Alto"
    }
}

def criar_agente(_vectorstore, _memory, model_name="gpt-4o-mini"):
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
        model_name=model_name, 
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
    
    # Seletor de modelo
    st.markdown("### 🤖 Seleção de Modelo")
    modelo_selecionado = st.selectbox(
        "Escolha o modelo:",
        options=list(MODELOS_DISPONIVEIS.keys()),
        index=0,
        help="Selecione o modelo de linguagem para gerar as respostas"
    )
    
    # Informações do modelo selecionado
    modelo_info = MODELOS_DISPONIVEIS[modelo_selecionado]
    st.caption(f"💡 {modelo_info['descricao']} | 💰 Custo: {modelo_info['custo']}")
    
    # Opção de comparar modelos (melhor vs pior)
    st.markdown("---")
    comparar_modelos = st.checkbox(
        "🔄 Comparar melhor vs pior modelo",
        help="Compare GPT-4o (melhor) com GPT-3.5-turbo (mais econômico)"
    )
    
    if comparar_modelos:
        modelos_para_comparar = ["GPT-4o", "GPT-3.5-turbo"]
    else:
        modelos_para_comparar = [modelo_selecionado]
  
    if st.button("🗑️ Limpar Histórico"):
        st.session_state.messages = []
        st.session_state.memory.clear()
        st.session_state.memories_modelos = {}
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
    st.info(f"""
    **Modelo Atual:** {modelo_selecionado}  
    **Técnica:** RAG (Retrieval Augmented Generation)  
    **Vectorstore:** FAISS com MMR  
    **Cache:** Ativado
    
    **Documentos incluídos:**
    - PDF: Instruções de Preenchimento
    - XLS: Leiaute do Documento
    - XLS: Críticas e Validações
    - XML: Exemplo de Estrutura
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
    
    # Processa com os modelos selecionados
    respostas_modelos = {}
    
    if len(modelos_para_comparar) == 1:
        # Modo simples: um modelo
        modelo_nome = modelos_para_comparar[0]
        modelo_key = MODELOS_DISPONIVEIS[modelo_nome]["nome"]
        
        with st.chat_message("assistant"):
            with st.spinner(f"🤔 Analisando com {modelo_nome}..."):
                try:
                    # Usa memória compartilhada ou cria uma específica
                    if modelo_nome in st.session_state.memories_modelos:
                        memoria_modelo = st.session_state.memories_modelos[modelo_nome]
                    else:
                        memoria_modelo = ConversationBufferMemory(
                            memory_key="chat_history",
                            return_messages=True,
                            output_key="answer"
                        )
                        st.session_state.memories_modelos[modelo_nome] = memoria_modelo
                    
                    agente = criar_agente(vectorstore, memoria_modelo, model_name=modelo_key)
                    resultado = agente.invoke({"question": pergunta})
                    resposta = resultado["answer"]
                    documentos_fonte = resultado.get("source_documents", [])
                    
                    st.markdown(resposta)
                    
                    # Busca complementar na internet
                    try:
                        search = DuckDuckGoSearchRun()
                        resultado_web = search.run(f"SCR 3040 Banco Central {pergunta}")
                        if resultado_web and len(resultado_web.strip()) > 0:
                            with st.expander("🌐 Informação complementar da internet"):
                                st.write(resultado_web)
                    except:
                        pass
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": resposta,
                        "modelo": modelo_nome,
                        "sources": documentos_fonte
                    })
                    
                except Exception as e:
                    erro_msg = f"❌ Erro ao processar pergunta: {str(e)}"
                    st.error(erro_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": erro_msg,
                        "modelo": modelo_nome
                    })
    else:
        # Modo comparação: melhor vs pior (2 modelos lado a lado)
        st.markdown("### 🔄 Comparação: Melhor vs Mais Econômico")
        
        col1, col2 = st.columns(2)
        respostas_modelos = {}
        
        for idx, modelo_nome in enumerate(modelos_para_comparar):
            modelo_key = MODELOS_DISPONIVEIS[modelo_nome]["nome"]
            col = col1 if idx == 0 else col2
            
            with col:
                st.markdown(f"#### 🤖 {modelo_nome}")
                st.caption(f"{MODELOS_DISPONIVEIS[modelo_nome]['descricao']} | 💰 {MODELOS_DISPONIVEIS[modelo_nome]['custo']}")
                
                with st.spinner(f"Processando {modelo_nome}..."):
                    try:
                        # Usa ou cria memória específica para cada modelo
                        if modelo_nome in st.session_state.memories_modelos:
                            memoria_modelo = st.session_state.memories_modelos[modelo_nome]
                        else:
                            memoria_modelo = ConversationBufferMemory(
                                memory_key="chat_history",
                                return_messages=True,
                                output_key="answer"
                            )
                            st.session_state.memories_modelos[modelo_nome] = memoria_modelo
                        
                        agente = criar_agente(vectorstore, memoria_modelo, model_name=modelo_key)
                        resultado = agente.invoke({"question": pergunta})
                        resposta = resultado["answer"]
                        documentos_fonte = resultado.get("source_documents", [])
                        
                        respostas_modelos[modelo_nome] = resposta
                        
                        st.markdown("**Resposta:**")
                        st.markdown(resposta)
                        
                        # Informações adicionais (sem expander)
                        st.caption(f"📄 Documentos utilizados: {len(documentos_fonte)}")
                        
                    except Exception as e:
                        erro_msg = f"❌ Erro: {str(e)}"
                        st.error(erro_msg)
                        respostas_modelos[modelo_nome] = erro_msg
        
        # Resumo comparativo simples
        if len(respostas_modelos) == 2:
            st.markdown("---")
            st.markdown("### 📊 Comparação Rápida")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                comprimentos = [len(r) for r in respostas_modelos.values() if isinstance(r, str) and not r.startswith("❌")]
                if comprimentos:
                    st.metric("Tamanho Médio", f"{sum(comprimentos)//len(comprimentos)} chars")
            with col2:
                modelos_sucesso = [m for m, r in respostas_modelos.items() if isinstance(r, str) and not r.startswith("❌")]
                st.metric("Modelos com Sucesso", len(modelos_sucesso))
            with col3:
                if len(modelos_sucesso) == 2:
                    melhor = max(modelos_para_comparar, key=lambda m: len(respostas_modelos.get(m, "")))
                    st.metric("Resposta Mais Detalhada", melhor)
        
        # Salva todas as respostas no histórico
        for modelo_nome, resposta in respostas_modelos.items():
            st.session_state.messages.append({
                "role": "assistant",
                "content": resposta,
                "modelo": modelo_nome
            })



# rodar streamlit run agente/app_melhorado.py