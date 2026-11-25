FROM python:3.12-slim

# System dependencies for Pillow advanced text rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    libraqm0 \
    libfribidi0 \
    libharfbuzz0b \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt 'streamlit[auth]==1.67.0' \
    && python deploy/install_pwa.py \
    && useradd --create-home litlas \
    && chown -R litlas:litlas /app/.litlas_assets \
    && mkdir -p /home/litlas/.streamlit \
    && ln -s /etc/secrets/secrets.toml /home/litlas/.streamlit/secrets.toml

# Verify Pillow RAQM support
RUN python -c "from PIL import features; assert features.check_feature('raqm'), 'RAQM unavailable'; print('RAQM support: OK')"

USER litlas
ENV LITLAS_DB_BACKEND=postgres
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

CMD ["sh", "-c", "exec python -m streamlit run src/litlas/app/main.py --server.port \"${PORT:-10000}\""]