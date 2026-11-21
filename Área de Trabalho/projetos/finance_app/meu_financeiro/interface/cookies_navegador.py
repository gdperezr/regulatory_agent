"""Lê e grava cookies do navegador para o lembrete de entrada."""

import json

import streamlit as st
import streamlit.components.v2

_COMPONENTE = st.components.v2.component(
    name="meu_financeiro.cookies_navegador",
    js="""
    function decodeCookiePart(value) {
      try {
        return decodeURIComponent(value);
      } catch (_error) {
        return value;
      }
    }

    function parseCookies() {
      const snapshot = {};
      const rawCookie = document.cookie || "";
      if (!rawCookie.trim()) {
        return snapshot;
      }
      rawCookie.split(";").forEach((part) => {
        const trimmed = part.trim();
        if (!trimmed) {
          return;
        }
        const separatorIndex = trimmed.indexOf("=");
        const rawName = separatorIndex >= 0 ? trimmed.slice(0, separatorIndex) : trimmed;
        const rawValue = separatorIndex >= 0 ? trimmed.slice(separatorIndex + 1) : "";
        snapshot[decodeCookiePart(rawName)] = decodeCookiePart(rawValue);
      });
      return snapshot;
    }

    function buildCookieAttributes(options, includeExpiryReset) {
      const attributes = ["path=/", "samesite=lax"];
      const normalized = options ?? {};
      if (includeExpiryReset) {
        attributes.push("expires=Thu, 01 Jan 1970 00:00:00 GMT");
        attributes.push("max-age=0");
      } else if (normalized.max_age !== undefined && normalized.max_age !== null) {
        attributes.push(`max-age=${normalized.max_age}`);
      }
      if (normalized.secure) {
        attributes.push("secure");
      }
      return attributes;
    }

    function setCookie(name, value, options) {
      const attributes = buildCookieAttributes(options, false);
      document.cookie = [
        `${encodeURIComponent(name)}=${encodeURIComponent(value)}`,
        ...attributes,
      ].join("; ");
    }

    function deleteCookie(name, options) {
      const attributes = buildCookieAttributes(options, true);
      document.cookie = [`${encodeURIComponent(name)}=`, ...attributes].join("; ");
    }

    export default function (component) {
      const { data, setStateValue } = component;
      const operations = data?.operations ?? [];
      let lastProcessedOperationId = data?.last_processed_operation_id ?? 0;

      operations.forEach((operation) => {
        if (operation.type === "set") {
          setCookie(operation.name, operation.value, operation.options);
        } else if (operation.type === "delete") {
          deleteCookie(operation.name, operation.options);
        }
        lastProcessedOperationId = Math.max(
          lastProcessedOperationId,
          operation.id ?? lastProcessedOperationId
        );
      });

      const sorted = Object.entries(parseCookies()).sort(([left], [right]) =>
        left.localeCompare(right)
      );
      setStateValue("ready", true);
      setStateValue("snapshot_json", JSON.stringify(Object.fromEntries(sorted)));
      setStateValue("last_processed_operation_id", lastProcessedOperationId);
      return () => {};
    }
    """,
)


def _ao_sincronizar() -> None:
    return None


class CookiesNavegador:
    """Cookies visíveis ao JavaScript. O componente precisa de uma atualização para ler o navegador."""

    def __init__(self, chave: str = "mf_cookies"):
        self._chave = chave
        self._estado = st.session_state.setdefault(
            f"{chave}__estado",
            {"proximo_id": 1, "pendentes": []},
        )
        estado_componente = st.session_state.get(chave, {})
        ultimo_id = estado_componente.get("last_processed_operation_id", 0)
        if ultimo_id:
            self._estado["pendentes"] = [
                operacao for operacao in self._estado["pendentes"] if operacao["id"] > ultimo_id
            ]
        with st._event:
            resultado = _COMPONENTE(
                key=chave,
                data={
                    "operations": self._estado["pendentes"],
                    "last_processed_operation_id": ultimo_id,
                },
                default={
                    "ready": estado_componente.get("ready", False),
                    "snapshot_json": estado_componente.get("snapshot_json", "{}"),
                    "last_processed_operation_id": ultimo_id,
                },
                on_ready_change=_ao_sincronizar,
                on_snapshot_json_change=_ao_sincronizar,
                on_last_processed_operation_id_change=_ao_sincronizar,
                height=0,
            )
        self._pronto = bool(resultado.ready)
        self._cookies = json.loads(resultado.snapshot_json or "{}")
        self._seguro = str(getattr(st.context, "url", "") or "").startswith("https://")

    def pronto(self) -> bool:
        return self._pronto

    def obter(self, nome: str) -> str | None:
        valor = self._cookies.get(nome)
        return valor if valor else None

    def gravar(self, nome: str, valor: str, segundos: int) -> None:
        self._enfileirar("set", nome, valor, segundos)

    def apagar(self, nome: str) -> None:
        self._enfileirar("delete", nome, None, None)

    def _enfileirar(self, tipo: str, nome: str, valor: str | None, segundos: int | None) -> None:
        opcoes: dict[str, str | int | bool] = {"secure": self._seguro}
        if segundos is not None:
            opcoes["max_age"] = segundos
        operacao_id = self._estado["proximo_id"]
        self._estado["proximo_id"] += 1
        self._estado["pendentes"].append(
            {"id": operacao_id, "type": tipo, "name": nome, "value": valor, "options": opcoes}
        )
