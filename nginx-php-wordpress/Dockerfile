FROM alpine:3.10.1

#LABEL sh.demyx.image demyx/nginx-php-wordpress
#LABEL sh.demyx.maintainer Demyx <info@demyx.sh>
#LABEL sh.demyx.url https://demyx.sh
#LABEL sh.demyx.github https://github.com/demyxco/demyx
#LABEL sh.demyx.registry https://hub.docker.com/u/demyx

ENV TZ America/Los_Angeles
ENV NGINX_VERSION 1.17.3
ENV NJS_VERSION   0.3.5
ENV PKG_RELEASE   1
ENV NGX_CACHE_PURGE_VERSION 2.3
ENV HEADERS_MORE_NGINX_MODULE_VERSION 0.33
ENV WORDPRESS_VERSION 5.2.2
ENV WORDPRESS_SHA1 3605bcbe9ea48d714efa59b0eb2d251657e7d5b0
ENV LISTEN_PORT 80

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories \
    && set -x \
# create nginx user/group first, to be consistent throughout docker variants
    && addgroup -g 101 -S nginx \
    && adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx \
    && apkArch="$(cat /etc/apk/arch)" \
    && nginxPackages=" \
        nginx=${NGINX_VERSION}-r${PKG_RELEASE} \
        nginx-module-xslt=${NGINX_VERSION}-r${PKG_RELEASE} \
        nginx-module-geoip=${NGINX_VERSION}-r${PKG_RELEASE} \
        nginx-module-image-filter=${NGINX_VERSION}-r${PKG_RELEASE} \
        nginx-module-njs=${NGINX_VERSION}.${NJS_VERSION}-r${PKG_RELEASE} \
    " \
    && case "$apkArch" in \
        x86_64) \
# arches officially built by upstream
            set -x \
            && KEY_SHA512="e7fa8303923d9b95db37a77ad46c68fd4755ff935d0a534d26eba83de193c76166c68bfe7f65471bf8881004ef4aa6df3e34689c305662750c0172fca5d8552a *stdin" \
            && apk add --no-cache --virtual .cert-deps \
                openssl curl ca-certificates \
            && curl -o /tmp/nginx_signing.rsa.pub https://nginx.org/keys/nginx_signing.rsa.pub \
            && if [ "$(openssl rsa -pubin -in /tmp/nginx_signing.rsa.pub -text -noout | openssl sha512 -r)" = "$KEY_SHA512" ]; then \
                 echo "key verification succeeded!"; \
                 mv /tmp/nginx_signing.rsa.pub /etc/apk/keys/; \
               else \
                 echo "key verification failed!"; \
                 exit 1; \
               fi \
            && printf "%s%s%s\n" \
                "https://nginx.org/packages/mainline/alpine/v" \
                `egrep -o '^[0-9]+\.[0-9]+' /etc/alpine-release` \
                "/main" \
            | tee -a /etc/apk/repositories \
            && apk del .cert-deps \
            ;; \
        *) \
# we're on an architecture upstream doesn't officially build for
# let's build binaries from the published packaging sources
            set -x \
            && tempDir="$(mktemp -d)" \
            && chown nobody:nobody $tempDir \
            && apk add --no-cache --virtual .build-deps \
                gcc \
                libc-dev \
                make \
                openssl-dev \
                pcre-dev \
                zlib-dev \
                linux-headers \
                libxslt-dev \
                gd-dev \
                geoip-dev \
                perl-dev \
                libedit-dev \
                mercurial \
                bash \
                alpine-sdk \
                findutils \
            && su - nobody -s /bin/sh -c " \
                export HOME=${tempDir} \
                && cd ${tempDir} \
                && hg clone https://hg.nginx.org/pkg-oss \
                && cd pkg-oss \
                && hg up ${NGINX_VERSION}-${PKG_RELEASE} \
                && cd alpine \
                && make all \
                && apk index -o ${tempDir}/packages/alpine/${apkArch}/APKINDEX.tar.gz ${tempDir}/packages/alpine/${apkArch}/*.apk \
                && abuild-sign -k ${tempDir}/.abuild/abuild-key.rsa ${tempDir}/packages/alpine/${apkArch}/APKINDEX.tar.gz \
                " \
            && echo "${tempDir}/packages/alpine/" >> /etc/apk/repositories \
            && cp ${tempDir}/.abuild/abuild-key.rsa.pub /etc/apk/keys/ \
            && apk del .build-deps \
            ;; \
    esac \
    && apk add --no-cache $nginxPackages \
# if we have leftovers from building, let's purge them (including extra, unnecessary build deps)
    && if [ -n "$tempDir" ]; then rm -rf "$tempDir"; fi \
    && if [ -n "/etc/apk/keys/abuild-key.rsa.pub" ]; then rm -f /etc/apk/keys/abuild-key.rsa.pub; fi \
    && if [ -n "/etc/apk/keys/nginx_signing.rsa.pub" ]; then rm -f /etc/apk/keys/nginx_signing.rsa.pub; fi \
# remove the last line with the packages repos in the repositories file
    && sed -i '$ d' /etc/apk/repositories \
# Bring in gettext so we can get `envsubst`, then throw
# the rest away. To do this, we need to install `gettext`
# then move `envsubst` out of the way so `gettext` can
# be deleted completely, then move `envsubst` back.
    && apk add --no-cache --virtual .gettext gettext \
    && mv /usr/bin/envsubst /tmp/ \
    \
    && runDeps="$( \
        scanelf --needed --nobanner /tmp/envsubst \
            | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
            | sort -u \
            | xargs -r apk info --installed \
            | sort -u \
    )" \
    && apk add --no-cache $runDeps \
    && apk del .gettext \
    && mv /tmp/envsubst /usr/local/bin/ \
# Bring in tzdata so users could set the timezones through the environment
# variables
    && apk add --no-cache tzdata curl \
# forward request and error logs to docker log collector
    && ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log

#    
# BUILD CUSTOM MODULES
#
RUN apk add --no-cache --virtual .build-deps \
	gcc \
	libc-dev \
	make \
	openssl-dev \
	pcre-dev \
	zlib-dev \
	linux-headers \
	curl \
	gnupg1 \
	libxslt-dev \
	gd-dev \
	geoip-dev \
	\
	&& mkdir -p /usr/src \
	&& curl -o ngx_cache_purge.tar.gz -fSL "https://github.com/FRiCKLE/ngx_cache_purge/archive/${NGX_CACHE_PURGE_VERSION}.tar.gz" \
	&& tar -xzf ngx_cache_purge.tar.gz -C /usr/src/ \
	&& rm ngx_cache_purge.tar.gz \
	&& curl -o headers-more-nginx-module.tar.gz -fSL "https://github.com/openresty/headers-more-nginx-module/archive/v${HEADERS_MORE_NGINX_MODULE_VERSION}.tar.gz" \
	&& tar -xzf headers-more-nginx-module.tar.gz -C /usr/src/ \
	&& rm headers-more-nginx-module.tar.gz \
	&& curl -o nginx.tar.gz -fSL "https://nginx.org/download/nginx-${NGINX_VERSION}.tar.gz" \
	&& tar -xzf nginx.tar.gz -C /usr/src/ \
	&& rm nginx.tar.gz \
	&& sed -i "s/HTTP_MODULES/#HTTP_MODULES/g" /usr/src/ngx_cache_purge-"$NGX_CACHE_PURGE_VERSION"/config \
	&& sed -i "s/NGX_ADDON_SRCS/#NGX_ADDON_SRCS/g" /usr/src/ngx_cache_purge-"$NGX_CACHE_PURGE_VERSION"/config \
	&& sed -i "s|ngx_addon_name=ngx_http_cache_purge_module|ngx_addon_name=ngx_http_cache_purge_module; if test -n \"\$ngx_module_link\"; then ngx_module_type=HTTP; ngx_module_name=ngx_http_cache_purge_module; ngx_module_srcs=\"\$ngx_addon_dir/ngx_cache_purge_module.c\"; . auto/module; else HTTP_MODULES=\"\$HTTP_MODULES ngx_http_cache_purge_module\"; NGX_ADDON_SRCS=\"\$NGX_ADDON_SRCS \$ngx_addon_dir/ngx_cache_purge_module.c\"; fi|g" /usr/src/ngx_cache_purge-${NGX_CACHE_PURGE_VERSION}/config \
	&& sed -i "s|ngx_addon_name=ngx_http_headers_more_filter_module|ngx_addon_name=ngx_http_headers_more_filter_module; if test -n \"\$ngx_module_link\"; then ngx_module_type=HTTP; ngx_module_name=ngx_http_headers_more_filter_module; ngx_module_srcs=\"\$ngx_addon_dir/ngx_http_headers_more_filter_module.c\"; . auto/module; else HTTP_MODULES=\"\$HTTP_MODULES ngx_http_headers_more_filter_module\"; NGX_ADDON_SRCS=\"\$NGX_ADDON_SRCS \$ngx_addon_dir/ngx_http_headers_more_filter_module.c\"; fi|g" /usr/src/headers-more-nginx-module-${HEADERS_MORE_NGINX_MODULE_VERSION}/config \
	&& cd /usr/src/nginx-"$NGINX_VERSION" \
	&& ./configure --with-compat --add-dynamic-module=/usr/src/ngx_cache_purge-"$NGX_CACHE_PURGE_VERSION" \
	&& make modules \
	&& cp objs/ngx_http_cache_purge_module.so /etc/nginx/modules \
	&& make clean \
	&& ./configure --with-compat --add-dynamic-module=/usr/src/headers-more-nginx-module-"$HEADERS_MORE_NGINX_MODULE_VERSION" \
	&& make modules \
	&& cp objs/ngx_http_headers_more_filter_module.so /etc/nginx/modules \
	&& rm -rf /usr/src/nginx-"$NGINX_VERSION" /usr/src/ngx_cache_purge-"$NGX_CACHE_PURGE_VERSION" /usr/src/headers-more-nginx-module-"$HEADERS_MORE_NGINX_MODULE_VERSION" \
	&& apk del .build-deps \
    && rm -rf /var/cache/apk/*
#    
# END BUILD CUSTOM MODULES
#

RUN set -ex; \
    adduser -u 82 -D -S -G  www-data www-data; \
    apk add --no-cache php7 \
    php7-bcmath \
    php7-ctype \
	php7-curl \
	php7-dom \
	php7-exif \
    php7-fileinfo \
    php7-fpm \
	php7-ftp \
	php7-gd \
    php7-gmp \
	php7-iconv \
	php7-imagick \
	php7-json \
	php7-mbstring \
	php7-mysqli \
    php7-opcache \
	php7-openssl \
    php7-pecl-mcrypt \
    php7-pecl-ssh2 \
    php7-pecl-redis \
    php7-phar \
	php7-posix \
    php7-session \
	php7-simplexml \
    php7-soap \
    php7-sodium \
	php7-sockets \
	php7-tokenizer \
	php7-xml \
	php7-xmlreader \
    php7-xmlwriter \
    php7-zip \
	php7-zlib

RUN set -ex; \
	apk add --no-cache ed dumb-init bash libsodium; \
    ln -s /usr/sbin/php-fpm7 /usr/local/bin/php-fpm; \
    mkdir -p /var/log/demyx



RUN set -ex; \
    apk add --no-cache --virtual .wp-deps curl; \
    mkdir -p /var/www/html; \
	curl -o wordpress.tar.gz -fSL "https://wordpress.org/wordpress-${WORDPRESS_VERSION}.tar.gz"; \
	echo "$WORDPRESS_SHA1 *wordpress.tar.gz" | sha1sum -c -; \
	tar -xzf wordpress.tar.gz -C /usr/src/; \
	rm wordpress.tar.gz; \
	chown -R www-data:www-data /usr/src/wordpress; \
    apk del .wp-deps && rm -rf /var/cache/apk/*

COPY common /etc/nginx/common
COPY cache /etc/nginx/cache
COPY demyx-entrypoint.sh /usr/local/bin/demyx-entrypoint
#TODO use nginx.conf.tml
COPY nginx.conf /etc/nginx/nginx.conf
COPY php.ini /etc/php7/php.ini
COPY www.conf /etc/php7/php-fpm.d/www.conf
COPY docker.conf /etc/php7/php-fpm.d/docker.conf

RUN chmod +x /usr/local/bin/demyx-entrypoint

EXPOSE 80

WORKDIR /var/www/html

ENTRYPOINT ["dumb-init", "demyx-entrypoint"]
