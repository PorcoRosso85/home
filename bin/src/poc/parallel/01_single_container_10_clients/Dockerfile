FROM denoland/deno:alpine-2.2.12

WORKDIR /app

# Copy source files
COPY deno.json ./
COPY server.ts ./

# Cache dependencies
RUN deno cache server.ts

EXPOSE 3000

CMD ["run", "--allow-net", "--allow-env", "server.ts"]