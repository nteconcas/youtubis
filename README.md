# 🎬 TubeDL - YouTube Downloader Web

Aplicativo web em Flask para baixar músicas e vídeos do YouTube, com interface moderna usando **Jinja2**, **Tailwind CSS** e **Font Awesome**.

---

## 📋 Requisitos

- **Python 3.10+**
- **FFmpeg** (obrigatório para conversão de áudio e merge de vídeo+audio)
- Dependências Python (veja `requirements.txt`)

### Instalando o FFmpeg

**Windows:**
1. Baixe em https://www.gyan.dev/ffmpeg/builds/
2. Extraia e adicione a pasta `bin/` à variável PATH
3. Verifique: `ffmpeg -version`

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt update && sudo apt install ffmpeg
```

---

## 🚀 Instalação

```bash
# 1. Clone ou baixe os arquivos
# 2. Acesse a pasta do projeto
cd youtube_downloader_web

# 3. Crie um ambiente virtual (recomendado)
python -m venv venv

# 4. Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 5. Instale as dependências
pip install -r requirements.txt

# 6. Execute o aplicativo
python app.py
```

O site estará disponível em: **http://localhost:5000**

---

## 🖥️ Estrutura do Projeto

```
youtube_downloader_web/
├── app.py                  # Aplicação Flask principal
├── requirements.txt        # Dependências Python
├── downloads/              # Pasta de downloads (auto-criada)
├── static/
│   ├── css/
│   │   └── style.css       # Estilos customizados
│   ├── js/
│   │   └── main.js         # JavaScript interativo
│   └── img/                # Imagens (opcional)
└── templates/
    ├── base.html           # Template base (Jinja2)
    ├── index.html          # Página inicial
    ├── info.html           # Informações do vídeo
    ├── formats.html        # Lista de formatos
    ├── history.html        # Histórico de downloads
    ├── download.html       # Status de download
    └── error.html          # Página de erro
```

---

## 🎨 Tecnologias Frontend

| Tecnologia | Uso |
|-----------|-----|
| **Jinja2** | Templates HTML dinâmicos |
| **Tailwind CSS** | Estilização via CDN |
| **Font Awesome 6** | Ícones vetoriais |
| **Google Fonts (Inter)** | Tipografia moderna |
| **Vanilla JS** | Interatividade do frontend |

---

## ⚡ Funcionalidades

| Recurso | Descrição |
|---------|-----------|
| ✅ Análise de URL | Extrai informações do vídeo antes de baixar |
| ✅ Vídeo MP4 | Download em múltiplas resoluções (360p a 8K) |
| ✅ Áudio | MP3, M4A, FLAC, OGG, OPUS, WAV com metadados ID3 |
| ✅ Playlists | Download completo de playlists |
| ✅ Formatos | Lista todos os formatos disponíveis do YouTube |
| ✅ Thumbnail | Incorpora capa do vídeo nos arquivos de áudio |
| ✅ Metadados | Título, artista, descrição embedados |
| ✅ Histórico | Registro dos últimos 100 downloads |
| ✅ Limpeza Auto | Remove arquivos antigos automaticamente |
| ✅ Validação | Verificação de URLs do YouTube |
| ✅ Interface Web | Design moderno e responsivo |

---

## 🌐 Deploy na Rede da Escola

### Opção 1: Flask em Modo de Desenvolvimento
```bash
python app.py
# Acesse: http://IP_DO_SERVIDOR:5000
```

### Opção 2: Gunicorn (Produção)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Opção 3: Docker
```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y ffmpeg
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### Configuração de Rede
Para acessar de outros computadores na rede da escola:

1. Verifique o IP do servidor:
```bash
# Windows
ipconfig
# Linux/macOS
ip addr show
```

2. Acesse pelo navegador:
```
http://IP_DO_SERVIDOR:5000
```

3. Para porta fixa, configure no `app.py`:
```python
app.run(host="0.0.0.0", port=5000)
```

---

## 🔒 Segurança

- Arquivos são salvos localmente no servidor
- Limpeza automática a cada 24 horas
- Validação de URLs do YouTube
- Limite de 100 itens no histórico

---

## ⚠️ Aviso Legal

Este aplicativo é destinado apenas para **uso pessoal e educacional**. Respeite os direitos autorais e os Termos de Serviço do YouTube.

---

## 🛠️ Tecnologias Backend

- [Flask](https://flask.palletsprojects.com/) - Framework web
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Download engine
- [FFmpeg](https://ffmpeg.org/) - Processamento de mídia

---

## 📄 Licença

MIT License - Uso livre para fins educacionais e pessoais.
