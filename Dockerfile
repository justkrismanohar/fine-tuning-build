# CivicDesk course image: Jupyter + OLMo + Phi weights baked in at build.
#
# Layer order matters: the model download is BEFORE copying notebooks, so
# editing T1-01 etc. does not re-download OLMo/Phi.
#
#   Jupyter  :8888
#   OLMo     :8000/v1
#   Phi      :8001/v1
# In T1-01 set BACKEND = "local".

FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SHELL=/bin/bash \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/models/hf-cache \
    CIVICDESK_MODELS_DIR=/models \
    TOKENIZERS_PARALLELISM=false

RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        ca-certificates \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /civicdesk

COPY environment/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch \
    && pip install --no-cache-dir transformers==4.46.3 accelerate sentencepiece protobuf jinja2==3.1.6 "huggingface_hub[hf_transfer]"

# Bake weights first (slow). Cached unless this script or CIVICDESK_DOWNLOAD changes.
ARG HF_TOKEN=
ENV HF_TOKEN=$HF_TOKEN \
    HF_HUB_ENABLE_HF_TRANSFER=1
COPY environment/download_models.py /tmp/download_models.py
RUN sed -i 's/\r$//' /tmp/download_models.py \
    && python /tmp/download_models.py

# Notebooks and helpers — changing these does not redo the download layer.
COPY . /opt/civicdesk
RUN sed -i 's/\r$//' /opt/civicdesk/environment/docker-entrypoint.sh \
    && chmod +x /opt/civicdesk/environment/docker-entrypoint.sh \
    && cp /opt/civicdesk/environment/docker-entrypoint.sh /usr/local/bin/course-entrypoint.sh \
    && mkdir -p /civicdesk

EXPOSE 8888 8000 8001

ENTRYPOINT ["/usr/local/bin/course-entrypoint.sh"]
CMD ["jupyter", "lab", \
     "--ip=0.0.0.0", \
     "--allow-root", \
     "--no-browser", \
     "--ServerApp.token=", \
     "--ServerApp.password=", \
     "--ServerApp.root_dir=/civicdesk"]