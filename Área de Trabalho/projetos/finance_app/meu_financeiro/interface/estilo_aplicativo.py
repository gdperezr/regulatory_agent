"""Aparência do Meu Financeiro: papel claro, verde e tipografia."""

from html import escape

import streamlit as st

_CSS = """
<style>
@import url("https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,560;9..144,640&family=Outfit:wght@400;500;600&display=swap");

html, body, [class*="css"], .stApp, .stApp p, .stApp label, .stApp input, .stApp textarea, .stApp button {
  font-family: "Outfit", "Segoe UI", sans-serif;
}

.stApp {
  background:
    radial-gradient(900px 420px at 100% -10%, rgba(31, 107, 74, 0.08), transparent 55%),
    #f3f0e8;
}

[data-testid="stHeader"] {
  background: transparent;
}

[data-testid="stToolbar"] {
  visibility: hidden;
}

footer {
  visibility: hidden;
}

.stMain .block-container {
  max-width: 1080px;
  padding-top: 1.6rem;
  padding-bottom: 3rem;
}

.mf-topo {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 1rem;
  margin: 0 0 0.4rem;
}

.mf-kicker {
  margin: 0;
  font-size: 0.72rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #7a6a58;
  font-weight: 600;
}

.mf-topo h1,
.st-key-cartao_login h1 {
  margin: 0.1rem 0 0;
  font-family: "Fraunces", Georgia, serif;
  font-weight: 560;
  font-size: 2.5rem;
  letter-spacing: -0.03em;
  line-height: 1.05;
  color: #1c2430;
}

.mf-ola {
  margin: 0 0 0.35rem;
  color: #5e675f;
  font-size: 1rem;
}

h2, h3, [data-testid="stHeading"] h3 {
  font-family: "Fraunces", Georgia, serif;
  letter-spacing: -0.02em;
  font-weight: 560;
}

[data-testid="stMetric"] {
  background: #fffdf8;
  border: 1px solid #e4ddd0;
  border-radius: 18px;
  padding: 0.85rem 1rem 0.7rem;
  box-shadow: 0 1px 2px rgba(28, 36, 48, 0.04);
}

[data-testid="stMetricLabel"] {
  color: #7a6a58;
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

[data-testid="stMetricValue"] {
  color: #1c2430;
  font-family: "Fraunces", Georgia, serif;
  font-weight: 560;
}

[data-testid="stForm"] {
  background: #fffdf8;
  border: 1px solid #e4ddd0;
  border-radius: 18px;
  padding: 0.6rem 1rem 0.2rem;
  box-shadow: 0 1px 2px rgba(28, 36, 48, 0.04);
}

.st-key-cartao_login {
  width: min(440px, 100%);
  align-self: center;
  margin-top: 8vh;
  background: #fffdf8;
  border: 1px solid #e4ddd0;
  border-top: 4px solid #1f6b4a;
  border-radius: 24px;
  padding: 1.6rem 1.5rem 0.6rem;
  box-shadow: 0 22px 50px rgba(31, 61, 50, 0.08);
}

.st-key-cartao_login [data-testid="stForm"] {
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 0.2rem 0 0;
}

.stTabs [data-baseweb="tab-list"] {
  gap: 0.35rem;
}

.stTabs [data-baseweb="tab"] {
  border-radius: 999px;
  padding: 0.4rem 0.95rem;
  background: transparent;
  color: #5e675f;
}

.stTabs [aria-selected="true"] {
  background: #1f3d32 !important;
  color: #f6f3ec !important;
}

.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {
  display: none;
}

.stButton > button,
.stFormSubmitButton > button {
  border-radius: 12px;
  font-weight: 560;
}

[data-testid="stDataFrame"] {
  border: 1px solid #e4ddd0;
  border-radius: 16px;
  overflow: hidden;
  background: #fffdf8;
}

[class*="st-key-mf_tabela"] {
  background: #fffdf8;
  border: 1px solid #e4ddd0;
  border-radius: 18px;
  padding: 0.15rem 0.85rem 0.2rem;
  margin: 0.15rem 0 1rem;
  box-shadow: 0 1px 2px rgba(28, 36, 48, 0.04);
}

[class*="st-key-mf_tabela"] [data-testid="stVerticalBlock"] {
  gap: 0;
}

[class*="st-key-mf_cabeca"] {
  border-bottom: 2px solid #1f3d32;
}

[class*="st-key-mf_linha"] {
  border-bottom: 1px solid #e4ddd0;
}

.mf-rotulo,
.mf-celula {
  margin: 0;
  line-height: 1.3;
  white-space: nowrap;
}

[class*="st-key-mf_tabela"] [data-testid="stHorizontalBlock"] {
  align-items: center;
}

[class*="st-key-mf_tabela"] [data-testid="column"] {
  padding-top: 0;
  padding-bottom: 0;
}

.mf-rotulo {
  padding: 0.55rem 0 0.45rem;
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #7a6a58;
  font-weight: 600;
}

.mf-celula {
  padding: 0.62rem 0;
  color: #1c2430;
  font-size: 0.95rem;
}

[class*="st-key-mf_tabela"] .stButton > button {
  border-radius: 999px;
  min-height: 2rem;
  padding: 0.15rem 0.7rem;
  font-size: 0.85rem;
  background: transparent;
  border: 1px solid #d9d0c3;
}

[class*="st-key-mf_tabela"] [data-testid="stForm"] {
  margin: 0.45rem 0 0.75rem;
}

[data-testid="stAlert"] {
  border-radius: 14px;
}

hr {
  border: none;
  border-top: 1px solid #e4ddd0;
  margin: 1.4rem 0;
}

[class*="st-key-mf_lista"] {
  background: #fffdf8;
  border: 1px solid #e4ddd0;
  border-radius: 14px;
  padding: 0.1rem 0.75rem 0.15rem;
  margin: 0.15rem 0 0.8rem;
}

[class*="st-key-mf_item"] {
  border-bottom: 1px solid #e4ddd0;
  padding: 0.35rem 0 0.4rem;
}

[class*="st-key-mf_item"]:last-of-type {
  border-bottom: none;
}

.mf-item-nome,
.mf-item-valor,
.mf-item-meta {
  margin: 0;
  line-height: 1.25;
}

.mf-item-nome {
  font-size: 1rem;
  font-weight: 600;
  color: #1c2430;
}

.mf-item-valor {
  font-size: 1rem;
  text-align: right;
  color: #1c2430;
  white-space: nowrap;
}

.mf-item-meta {
  font-size: 0.8rem;
  color: #7a6a58;
  white-space: normal;
}

[class*="st-key-mf_lista"] .stButton > button {
  border-radius: 999px;
  min-height: 1.8rem;
  padding: 0.05rem 0.55rem;
  font-size: 0.78rem;
  background: transparent;
  border: 1px solid #d9d0c3;
}

html {
  -webkit-text-size-adjust: 100%;
  text-size-adjust: 100%;
}

@media (max-width: 900px) {
  .stMain .block-container {
    padding-top: 0.7rem;
    padding-left: 0.7rem;
    padding-right: 0.7rem;
    padding-bottom: 1.5rem;
  }

  .mf-topo {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.15rem;
    margin-bottom: 0.15rem;
  }

  .mf-kicker {
    font-size: 0.62rem;
    letter-spacing: 0.12em;
  }

  .mf-topo h1,
  .st-key-cartao_login h1 {
    font-size: 1.45rem;
  }

  .mf-ola {
    margin: 0;
    font-size: 0.82rem;
  }

  .stTabs [data-baseweb="tab-list"] {
    gap: 0.15rem;
  }

  .stTabs [data-baseweb="tab-list"] {
    flex-wrap: wrap;
  }

  .stTabs [data-baseweb="tab"] {
    padding: 0.22rem 0.55rem;
    font-size: 0.78rem;
  }

  [data-testid="stHeaderActionElements"] {
    display: none !important;
  }

  h1, h2, h3,
  [data-testid="stHeading"] h1,
  [data-testid="stHeading"] h2,
  [data-testid="stHeading"] h3 {
    font-size: 1.2rem !important;
    line-height: 1.25 !important;
    padding-top: 0.55rem !important;
    padding-bottom: 0.15rem !important;
  }

  .mf-topo h1 {
    font-size: 1.45rem !important;
    line-height: 1.1 !important;
    padding: 0 !important;
  }

  [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {
    flex-wrap: nowrap !important;
    gap: 0.35rem !important;
  }

  [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="stColumn"] {
    min-width: 0 !important;
    width: auto !important;
    flex: 1 1 0% !important;
  }

  [data-testid="stMetric"] {
    padding: 0.38rem 0.4rem 0.28rem;
    border-radius: 12px;
  }

  [data-testid="stMetricLabel"],
  [data-testid="stMetricLabel"] * {
    font-size: 0.58rem !important;
    letter-spacing: 0.02em;
    line-height: 1.15 !important;
  }

  [data-testid="stMetricValue"],
  [data-testid="stMetricValue"] * {
    font-size: 0.92rem !important;
    line-height: 1.1 !important;
    white-space: nowrap;
  }

  [class*="st-key-mf_dash"] [data-testid="stVegaLiteChart"] {
    max-height: 210px;
  }

  [class*="st-key-mf_lista"] [data-testid="stHorizontalBlock"],
  [class*="st-key-mf_lista"] [data-testid="stColumn"],
  [class*="st-key-mf_lista"] [data-testid="stElementContainer"],
  [class*="st-key-mf_lista"] [data-testid="stMarkdown"] {
    height: auto !important;
    min-height: 1.15rem !important;
  }

  [class*="st-key-mf_lista"] [data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    gap: 0.3rem !important;
  }

  [class*="st-key-mf_lista"] [data-testid="stColumn"] {
    min-width: 0 !important;
    width: auto !important;
  }

  [class*="st-key-mf_lista"] .mf-item-nome,
  [class*="st-key-mf_lista"] .mf-item-valor {
    font-size: 0.9rem;
  }

  [class*="st-key-mf_lista"] .mf-item-meta {
    font-size: 0.68rem;
  }

  [class*="st-key-mf_lista"] .stButton > button {
    min-height: 1.65rem;
    padding: 0.05rem 0.4rem;
    font-size: 0.7rem;
  }

  [class*="st-key-mf_dash"] [data-testid="stCaptionContainer"] p {
    font-size: 0.75rem;
  }
}
</style>
"""


class EstiloAplicativo:
    def aplicar(self) -> None:
        st.markdown(_CSS, unsafe_allow_html=True)

    def topo(self, nome: str) -> None:
        saudacao = escape(nome.strip()) if nome else ""
        ola = f'<p class="mf-ola">Olá, {saudacao}</p>' if saudacao else ""
        st.markdown(
            f"""
            <header class="mf-topo">
              <div>
                <p class="mf-kicker">Finanças da casa</p>
                <h1>Meu Financeiro</h1>
              </div>
              {ola}
            </header>
            """,
            unsafe_allow_html=True,
        )
