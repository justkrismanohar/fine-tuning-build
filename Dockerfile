FROM nvcr.io/nvidia/pytorch:25.10-py3

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SHELL=/bin/bash \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_BREAK_SYSTEM_PACKAGES=1 \
    HF_HOME=/models/hf-cache \
    CIVICDESK_MODELS_DIR=/models \
    TOKENIZERS_PARALLELISM=false

RUN apt-get update && apt-get install -y --no-install-recommends \
        git ca-certificates build-essential curl tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /civicdesk

COPY environment/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && pip install --no-cache-dir "huggingface_hub[hf_transfer]" \
    pytesseract pypdf chromadb sentence_transformers \
    "transformers==4.53.3" "peft==0.14.0" accelerate sentencepiece \
    protobuf jinja2==3.1.6

ARG HF_TOKEN=
ENV HF_TOKEN=$HF_TOKEN \
    HF_XET_HIGH_PERFORMANCE=1

COPY environment/download_models.py /tmp/download_models.py
RUN sed -i 's/\r$//' /tmp/download_models.py \
    && python /tmp/download_models.py

RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

COPY ./environment/docker-entrypoint.sh  /opt/civicdesk/environment/docker-entrypoint.sh 
RUN sed -i 's/\r$//' /opt/civicdesk/environment/docker-entrypoint.sh \
    && chmod +x /opt/civicdesk/environment/docker-entrypoint.sh \
    && cp /opt/civicdesk/environment/docker-entrypoint.sh /usr/local/bin/course-entrypoint.sh \
    && mkdir -p /civicdesk

# Copy and enable the entrypoint script
COPY environment/load-course.sh /usr/local/bin/load-course.sh
RUN chmod +x /usr/local/bin/load-course.sh

# Run the script at container startup, passing CMD as arguments ($@)
ENTRYPOINT ["/usr/local/bin/load-course.sh"]

EXPOSE 8888 8000 8001

CMD ["jupyter", "lab", \
     "--ip=0.0.0.0", \
     "--allow-root", \
     "--no-browser", \
     "--ServerApp.token=", \
     "--ServerApp.password=", \
     "--ServerApp.root_dir=/civicdesk"]