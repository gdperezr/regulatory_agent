# Meu Financeiro

Cartões, compras parceladas e faturas. A tela é Streamlit. Os dados ficam no PostgreSQL. Cada pessoa entra com o próprio usuário e vê só os próprios lançamentos.

O servidor previsto é uma máquina Always Free da Oracle Cloud em São Paulo. Ela continua ligada com o computador de casa desligado. O iPhone chega nela pelo Tailscale, sem abrir o aplicativo para a internet.

## Estrutura

```
finance_app/
├── app.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── meu_financeiro/
    ├── dominio/
    ├── banco/
    ├── servicos/
    └── interface/
```

`app.py` só inicia o Streamlit. A pasta `banco/` fala com o PostgreSQL. A pasta `servicos/` calcula parcelas e confere senha. A pasta `interface/` desenha as abas.

## Neste computador

É preciso ter o Docker Desktop.

```powershell
copy .env.example .env
```

Edite `.env` com uma senha longa e o e-mail da primeira pessoa. Depois:

```powershell
docker compose up -d --build
```

Abra http://127.0.0.1:8501 e entre com o e-mail e a senha do `.env`. Na aba Conta, cadastre a segunda pessoa.

O arquivo antigo `data/financeiro.db` continua no disco. Com o compose no ar, para levar esses lançamentos ao PostgreSQL:

```powershell
docker compose run --rm -v "${PWD}/data:/app/data" --entrypoint python app -m meu_financeiro.banco.importador_sqlite
```

A cópia só ocorre se o PostgreSQL ainda não tiver cartões. O banco não recebe porta no computador: só o aplicativo, dentro do Docker, fala com ele.

## Oracle Cloud em São Paulo

1. Crie a conta em https://www.oracle.com/cloud/free/ escolhendo a região inicial **Brazil East (São Paulo)**. A conta pede cartão. Dentro do Always Free não há cobrança.
2. Em Billing, crie um orçamento mensal de R$ 0 e um alerta no seu e-mail.
3. Crie uma instância Ubuntu 24.04, forma **VM.Standard.A1.Flex** (Ampere), 1 OCPU e 6 GB. Isso já entra no gratuito e costuma ter vaga. 2 OCPUs e 12 GB também são gratuitos quando a região tem capacidade.
4. Marque a chave SSH. Na lista de segurança da rede, deixe entrada só na porta 22, a partir do IP da sua casa. Não abra 8501 nem 5432.
5. Entre por SSH, instale Docker e o Tailscale e suba o projeto:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Envie a pasta do projeto sem `venv/` e sem `.env`. Na máquina, copie `.env.example` para `.env`, preencha as senhas e execute `docker compose up -d --build`.

6. Publique a tela só na rede do Tailscale:

```bash
sudo tailscale serve --bg 8501
```

7. No iPhone, instale o Tailscale, entre na mesma conta e abra o endereço HTTPS que o comando `tailscale serve status` mostrar. A outra pessoa entra com o usuário criado na aba Conta.

O PostgreSQL fica só na rede interna do Docker. O Docker sobe de novo se a máquina reiniciar.

## Regras das faturas

- Compra no dia do fechamento ou depois entra na fatura do mês seguinte.
- Dia de fechamento 29, 30 ou 31 acompanha o último dia do mês curto.
- Parcelas são divididas em centavos e a soma fecha o total. O resto vai para as primeiras parcelas.
- O mês da fatura é o mês de fechamento, não o mês de vencimento.
- Na aba Compras, o PDF baixado no banco é lido e as despesas entram no mês escolhido depois da conferência. Parcela 3/10 lança só essa parcela. O mesmo PDF de novo não duplica. Foto e PDF com senha não são lidos.
- Ainda não há pagamento de fatura nem empréstimo.

## Backup

Na máquina da Oracle, pare só no momento da cópia e guarde o volume do Postgres. Com o compose no ar, um jeito simples é:

```bash
docker compose exec -T banco pg_dump -U financeiro financeiro > financeiro.sql
```

Guarde esse arquivo fora da máquina.
