⚡ Simulador de Circuitos Elétricos CA

Um projeto interativo para análise de circuitos de corrente alternada (CA) com visualizações gráficas e cálculos precisos.

Streamlit
GitHub license
Python
📌 Visão Geral

Este simulador permite modelar circuitos elétricos de corrente alternada (CA) com componentes R (Resistor), L (Indutor) e C (Capacitor), conectados em série ou paralelo. Ele calcula automaticamente:

    Impedância total (forma retangular e polar)

    Corrente, tensão e potências (Ativa, Reativa, Aparente)

    Fator de potência e ângulo de fase

    Diagramas fasoriais e resposta em frequência

✨ Funcionalidades

✅ Adição de componentes (R, L, C) em série ou paralelo
✅ Modo simples e avançado (insira diretamente impedância ou valores físicos de L e C)
✅ Análise completa com gráficos interativos
✅ Cálculos em tempo real de corrente, potência e fator de potência
✅ Visualização fasorial da impedância
✅ Resposta em frequência para circuitos RLC
🚀 Como Usar
1️⃣ Pré-requisitos

    Python 3.8+

    Bibliotecas: streamlit, matplotlib, numpy

2️⃣ Instalação
bash

git clone https://github.com/seu-usuario/simulador-circuitos-ca.git
cd simulador-circuitos-ca
pip install -r requirements.txt

3️⃣ Executando o Simulador
bash

streamlit run app.py

O aplicativo abrirá automaticamente no navegador.
📷 Demonstração
Interface Principal

Interface do Simulador
Exemplo de Cálculo RLC Série
Componente	Valor
Resistor (R)	100 Ω
Indutor (L)	j20 Ω
Capacitor (C)	-j10 Ω

Resultados:

    Impedância Total: 100 + j10 Ω

    Corrente: 1.194 A

    Potência Ativa (P): 142.57 W

    Fator de Potência: 0.995

📊 Gráficos Gerados
Diagrama Fasorial

Diagrama Fasorial
Resposta em Frequência

Resposta em Frequência
🔧 Tecnologias Utilizadas

    Python (Streamlit, Matplotlib, NumPy)

    GitHub (Hospedagem e versionamento)

📝 Licença

Este projeto está sob a licença MIT. Consulte o arquivo LICENSE para mais detalhes.
💡 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.
📌 Links Úteis

🔗 Acesse o App Online
📂 Repositório no GitHub

Desenvolvido com ❤️ por [Seu Nome]
⚡ Aprenda, simule e domine circuitos elétricos!
🎨 Personalize o README

    Substitua seu-usuario pelo seu nome de usuário no GitHub.

    Adicione screenshots reais do projeto.

    Inclua um link para o app hospedado (Streamlit Cloud, Heroku, etc.).
