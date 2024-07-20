# Englishfy

Englishfy é uma aplicação desenvolvida para facilitar o aprendizado da língua inglesa, integrando funcionalidades de ensino e práticas de conversação de maneira intuitiva e interativa.

## Visão Geral

Englishfy oferece uma plataforma onde os alunos podem melhorar suas habilidades de comunicação em inglês através de atividades didáticas, feedback imediato e orientação personalizada. 

## Funcionalidades

- **Aulas Didáticas**: Conjunto de atividades estruturadas para aprendizado progressivo.
- **Prática de Conversação**: Sessões interativas para praticar conversação em inglês.
- **Feedback Personalizado**: Respostas imediatas e orientações específicas para cada aluno.
- **Registro de Progresso**: Monitora e registra o progresso dos alunos ao longo do tempo.

Em breve novas funcionalidades.

## Tecnologias 

- **Backend**: Python
- **Contêineres**: Docker
- **IA's**: Google Gemini e Ollama3-70B (via Groq)
- **TTS** : IBM Watson text-to-speech

## Instalação

Siga os passos abaixo para configurar e executar a aplicação localmente:

1. Clone o repositório:
   ```sh
   git clone https://github.com/AlyssonM/Englishfy.git
   cd Englishfy
   ```
2. Crie um arquivo .env e configure suas variáveis de ambiente:
```sh
touch .env
```
Adicione as variáveis necessárias no arquivo .env:
```sh
GROQ_API_KEY={GROQ_API_KEY}
GOOGLE_API_KEY={GOOGLE_AI_API_KEY}
BOT_TOKEN={TELEGRAM_BOT_TOKEN}
DG_API_KEY={DEEPGRAM_BOT_TOKEN} //Optional
IBM_API_KEY={IBM_WATSON_API_KEY} // Default TTS provider
```

3. Construa a imagem Docker:
```sh
docker build -t englishfy .
```

4. Execute o contêiner:
```sh
docker run -d --env-file .env englishfy
```

# Uso

Depois de instalar e executar a aplicação, você pode acessar diferentes funcionalidades através da interface web. A aplicação permitirá que você:

* Participe de aulas didáticas.
* Pratique conversação com feedback em tempo real.
* Visualize seu progresso e estatísticas de aprendizado.


# Contato
Alysson M.
machally77@proton.me
