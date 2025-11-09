FROM python:3.14-slim-trixie AS base

FROM base AS dep

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update && \
    apt-get --no-install-recommends install -y \
        git \
        curl \
    ;

ARG username=searcher

# python package entrypoint will be generated with shebang, which records absolute path of venv python
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache \
    --mount=type=bind,source=uv.lock,target=/home/$username/searcher-mcp/uv.lock \
    --mount=type=bind,source=pyproject.toml,target=/home/$username/searcher-mcp/pyproject.toml \
    uv sync --directory /home/$username/searcher-mcp/ --locked --no-install-project --link-mode=copy --compile-bytecode && \
    uv run --directory /home/$username/searcher-mcp/ camoufox fetch --browserforge && \
    cp -r /root/.cache/camoufox /home/$username/camoufox

FROM base AS prod

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update && \
    apt-get --no-install-recommends install -y \
        libgtk-3-0t64 \
        libasound2 \
        libx11-xcb1 \
    ;

ARG username=searcher

RUN groupadd $username && useradd -m -g $username $username

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 UV_SYSTEM_PYTHON=1

USER $username
WORKDIR /home/$username/searcher-mcp
ENV PATH="/home/$username/searcher-mcp/.venv/bin:$PATH"

COPY --from=dep --chown=$username:$username /home/$username/searcher-mcp/.venv ./.venv
COPY --from=dep --chown=$username:$username /home/$username/camoufox /home/$username/.cache/camoufox

COPY --chown=$username:$username pyproject.toml uv.lock ./
COPY --chown=$username:$username searcher_mcp ./searcher_mcp
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    uv sync --locked --no-cache --compile-bytecode

ENTRYPOINT [ "fastmcp", "run", "searcher_mcp/server.py" ]
