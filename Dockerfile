FROM python:3.12-slim

WORKDIR /app

RUN groupadd --system poker-roots && \
    useradd --system --uid 10001 --gid poker-roots poker-roots && \
    mkdir /data && chown poker-roots:poker-roots /data

COPY --chown=poker-roots:poker-roots backend/ ./backend/
COPY --chown=poker-roots:poker-roots poker-roots-boceto/poker-roots/ ./poker-roots-boceto/poker-roots/

USER poker-roots
EXPOSE 8765

CMD ["python", "-m", "backend.api", "--host", "0.0.0.0", "--port", "8765", "--data-dir", "/data"]
