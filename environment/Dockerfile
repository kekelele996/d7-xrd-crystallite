FROM python:3.12.7-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 解题与参考解的身份由 task.toml 的 [agent] user = "runner" 指定。
# 容器默认用户保持 root：Harbor 的保活进程随默认用户运行，评分前清理 runner
# 进程时不能把它一起结束。
# curl/nodejs/npm/procps 是交互式解题工具的运行时，预装进镜像，避免每次评分
# 在容器里现装 node 时超时。
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl nodejs npm procps \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 runner \
    && pip install --no-cache-dir numpy==2.1.3 scipy==1.14.1

WORKDIR /app
COPY app/ /app/
RUN chown -R runner:runner /app
