FROM node:20-alpine AS client-build
WORKDIR /tmp/client
RUN apk add --no-cache git
RUN git clone --depth 1 -b feat/t8l50-smart-lock-c33 https://github.com/tale/eufy-security-client.git .
RUN npm ci --verbose --foreground-scripts
RUN npm run build --verbose
RUN npm pack

FROM node:20-alpine AS build
WORKDIR /tmp
RUN apk add --no-cache git
RUN git clone --depth 1 https://github.com/bropat/eufy-security-ws.git .
COPY --from=client-build /tmp/client/eufy-security-client-*.tgz /tmp/eufy-security-client.tgz
RUN npm pkg set dependencies.eufy-security-client="/tmp/eufy-security-client.tgz"
RUN rm package-lock.json
RUN npm install --verbose --foreground-scripts
RUN npm run build --verbose

FROM node:20-alpine AS prod
WORKDIR /tmp_prod
COPY --from=build /tmp/dist ./dist
COPY --from=build /tmp/docker/run.sh ./run.sh
COPY --from=build /tmp/package.json ./package.json
COPY --from=client-build /tmp/client/eufy-security-client-*.tgz ./eufy-security-client.tgz
RUN npm pkg set dependencies.eufy-security-client="./eufy-security-client.tgz"
RUN npm install --only=production

FROM node:20-alpine
WORKDIR /usr/src/app
COPY --from=prod /tmp_prod ./
RUN apk add --no-cache jq bash
EXPOSE 3000
VOLUME ["/data"]
CMD [ "/usr/src/app/run.sh" ]
